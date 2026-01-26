import pandas as pd
import io
import sys
import os
import json
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List
import time
import uuid

from dotenv import load_dotenv
from fpdf import FPDF

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --- Local Storage Configuration ---
EXPERIMENTS_DIR = Path("experiments")
LITERATURE_DIR = Path("literature")

class LocalStorageHandler:
    def __init__(self):
        EXPERIMENTS_DIR.mkdir(exist_ok=True)
        LITERATURE_DIR.mkdir(exist_ok=True)
        self._locks = {}
        self._locks_lock = threading.Lock()

    def _get_path(self, key: str) -> Path:
        # The key is the relative path, e.g., "experiments/exp_123/config.json"
        return Path(key)

    def read_json(self, key: str):
        path = self._get_path(key)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")

    def write_json(self, key: str, data: dict):
        path = self._get_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def write_file_content(self, key: str, content, content_type=None): # content_type is unused for local
        path = self._get_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        encoding = None if isinstance(content, bytes) else "utf-8"
        with open(path, mode, encoding=encoding) as f:
            f.write(content)

    def read_file_content(self, key: str):
        path = self._get_path(key)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")

    def list_dirs(self, prefix: str):
        path = Path(prefix)
        if not path.exists():
            return []
        # Sort by name descending, which is a good proxy for chronological order
        return sorted([d.name for d in path.iterdir() if d.is_dir()], reverse=True)

    def file_exists(self, key: str):
        return self._get_path(key).exists()

    def get_lock(self, key: str) -> threading.Lock:
        """Returns a lock for a specific file path to prevent race conditions."""
        with self._locks_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

storage_handler = LocalStorageHandler()

# --- Graceful Shutdown Support ---
shutdown_event = threading.Event()
active_tasks = set()
active_tasks_lock = threading.Lock()

# Load environment variables from .env file
load_dotenv()

# Add src directory to sys.path for module imports
# sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport
from src.modules.clinical import ClinicalAnalyzer
from src.modules.fhir_converter import FHIRConverter
from src.modules.literature import LiteratureSearch, LITERATURE_AVAILABLE
from src.modules.model_cache import ModelCache
from src.modules.constraint_manager import ConstraintManager, create_clinical_labs_template

# --- Caching and Constraint Manager Initialization ---
# Initialize the model cache. This will create a 'cache/models' directory.
model_cache = ModelCache(enabled=True)

# Initialize a default constraint manager with clinical constraints.
# In a more advanced setup, you might load different profiles based on user input.
clinical_constraint_manager = create_clinical_labs_template()

# --- Lifespan Context Manager for Graceful Shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("SynthLab API starting up...")
    yield
    # Shutdown
    print("Shutdown signal received. Waiting for background tasks to complete...")
    shutdown_event.set()

    # Wait for active tasks to complete (with timeout)
    max_wait = 30  # seconds
    waited = 0
    while waited < max_wait:
        with active_tasks_lock:
            if not active_tasks:
                break
            remaining = len(active_tasks)
        print(f"Waiting for {remaining} background task(s) to finish...")
        import asyncio
        await asyncio.sleep(1)
        waited += 1

    with active_tasks_lock:
        if active_tasks:
            print(f"Warning: {len(active_tasks)} task(s) did not complete within timeout")
        else:
            print("All background tasks completed. Shutting down cleanly.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="SynthLab API",
    description="API for generating privacy-safe synthetic data and performing literature analysis.",
    version="0.2.0",
    lifespan=lifespan
)

# --- CORS Middleware ---
# Support multiple origins for development and production
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Add production frontend URL if configured
if FRONTEND_URL:
    ALLOWED_ORIGINS.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Ollama Client Initialization ---
# Use a remote Ollama host if specified, otherwise default to local.
# --- In-Memory Storage for Literature Search ---
jobs = {}
literature_sessions = {}

# --- Pydantic Models ---
class NoteUpdate(BaseModel):
    notes: str

class GraphAnnotation(BaseModel):
    id: str = None
    graphId: str
    x: float
    y: float
    comment: str
    author: str = "Anonymous"
    timestamp: str = None
    resolved: bool = False

class LitSessionSave(BaseModel):
    name: str

class LitSearchRequest(BaseModel):
    session_id: str
    query: str


# --- Background Task Logic ---
def check_shutdown():
    """Check if shutdown has been requested."""
    return shutdown_event.is_set()

def run_synthesis_task(experiment_id: str, file_contents: bytes, method: str, num_rows: int, sensitive_column: str, epsilon: float, epochs: int = 300, sequence_key: str = None, sequence_index: str = None):
    exp_key_prefix = f"experiments/{experiment_id}"
    config_key = f"{exp_key_prefix}/config.json"

    # Register this task as active
    with active_tasks_lock:
        active_tasks.add(experiment_id)

    # Update in-memory job status
    jobs[experiment_id] = {"status": "running", "experiment_id": experiment_id}

    try:
        # Check for shutdown before starting
        if check_shutdown():
            raise InterruptedError("Shutdown requested before task started")

        # Update status to running
        config = storage_handler.read_json(config_key)
        config["status"] = "running"
        storage_handler.write_json(config_key, config)
        df = pd.read_csv(io.StringIO(file_contents.decode('utf-8')))
        loader = DataLoader()
        clean_df, _ = loader.clean_data(df)

        # Check for shutdown after data loading
        if check_shutdown():
            raise InterruptedError("Shutdown requested during data loading")

        # --- Clinical Analysis ---
        clinical_analyzer = ClinicalAnalyzer()
        clinical_analysis = clinical_analyzer.analyze_columns(clean_df)

        # Check for shutdown before training (most time-consuming step)
        if check_shutdown():
            raise InterruptedError("Shutdown requested before model training")

        # Pass epsilon, epochs, cache, and constraint manager to the generator
        # CTGAN and TVAE accept epochs as a model parameter
        model_params = {}
        if method in ['CTGAN', 'TVAE'] and epochs:
            model_params['epochs'] = epochs

        generator = SyntheticGenerator(
            method=method,
            model_params=model_params,
            epsilon=epsilon if epsilon > 0 else None,
            sequence_key=sequence_key,
            sequence_index=sequence_index,
            cache=model_cache,
            constraint_manager=clinical_constraint_manager
        )
        generator.train(clean_df)

        # Check for shutdown after training
        if check_shutdown():
            raise InterruptedError("Shutdown requested after model training")

        synthetic_data = generator.generate(num_rows)

        # Check for shutdown before report generation
        if check_shutdown():
            raise InterruptedError("Shutdown requested before report generation")

        quality_report = QualityReport(clean_df, synthetic_data)

        # --- Reports ---
        stats = quality_report.compare_stats()
        privacy_check = quality_report.check_privacy()
        ks_results = quality_report.ks_test()
        dcr = quality_report.distance_to_closest_record()

        fairness_results = None
        if sensitive_column and sensitive_column in synthetic_data.columns:
            if synthetic_data[sensitive_column].nunique() == 2:
                fairness_results = quality_report.flip_test(sensitive_column)

        # --- Plots ---
        dist_plots = quality_report.plot_distributions()
        corr_plots = quality_report.plot_correlation_heatmaps()
        dist_plots_json = {col: fig.to_json() for col, fig in dist_plots.items()}
        corr_plots_json = {'real': corr_plots[0].to_json(), 'synthetic': corr_plots[1].to_json(), 'diff': corr_plots[2].to_json()}

        # Save full report and data
        full_report = {**config, "status": "completed", "quality_report": {"column_stats": stats}, "privacy_report": {**privacy_check, "dcr": dcr}, "fairness_report": fairness_results, "plots": {"distributions": dist_plots_json, "correlations": corr_plots_json}, "clinical_report": clinical_analysis}
        storage_handler.write_json(f"{exp_key_prefix}/report.json", full_report)

        csv_buffer = io.StringIO()
        synthetic_data.to_csv(csv_buffer, index=False)
        storage_handler.write_file_content(f"{exp_key_prefix}/synthetic_data.csv", csv_buffer.getvalue())

        # Update in-memory job status to completed
        jobs[experiment_id] = {"status": "completed", "experiment_id": experiment_id, "result": full_report}

    except InterruptedError as e:
        print(f"Task {experiment_id} interrupted: {e}")
        config = storage_handler.read_json(config_key)
        config["status"] = "cancelled"
        config["error"] = str(e)
        storage_handler.write_json(config_key, config)
        jobs[experiment_id] = {"status": "cancelled", "error": str(e), "experiment_id": experiment_id}

    except Exception as e:
        print(f"Task failed: {e}")
        config = storage_handler.read_json(config_key)
        config["status"] = "failed"
        config["error"] = str(e)
        storage_handler.write_json(config_key, config)
        jobs[experiment_id] = {"status": "failed", "error": str(e), "experiment_id": experiment_id}

    finally:
        # Always unregister the task when done
        with active_tasks_lock:
            active_tasks.discard(experiment_id)

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the SynthLab API"}

@app.post("/api/synthesize")
async def synthesize_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    method: str = Form("CTGAN"),
    num_rows: int = Form(1000),
    sensitive_column: str = Form(None),
    epsilon: float = Form(0.0),
    epochs: int = Form(300),
    sequence_key: str = Form(None), # Column for Entity ID (e.g., PatientID)
    sequence_index: str = Form(None) # Column for Time/Order (e.g., VisitDate)
):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    try:
        contents = await file.read()
        
        experiment_id = f"exp_{uuid.uuid4().hex[:8]}"

        config = {
            "experiment_id": experiment_id,
            "method": method,
            "timestamp": pd.Timestamp.now().isoformat(),
            "num_rows": num_rows,
            "sensitive_column": sensitive_column,
            "epsilon": epsilon,
            "epochs": epochs,
            "sequence_key": sequence_key,
            "sequence_index": sequence_index,
            "status": "pending",
            # Add placeholders to prevent frontend crashes while processing
            "synthetic_data": [],
            "plots": None,
            "quality_report": {},
            "privacy_report": {},
            "clinical_report": {}
        }
        storage_handler.write_json(f"experiments/{experiment_id}/config.json", config)

        # Initialize job status
        jobs[experiment_id] = {"status": "pending", "experiment_id": experiment_id}

        # Offload heavy work to background task
        background_tasks.add_task(run_synthesis_task, experiment_id, contents, method, num_rows, sensitive_column, epsilon, epochs, sequence_key, sequence_index)

        return {"job_id": experiment_id, "status": "pending"}

    except Exception as e:
        print(f"An error occurred during synthesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/experiments")
def list_experiments():
    experiments = []
    exp_dirs = storage_handler.list_dirs('experiments')

    for exp_id in exp_dirs:
        config_key = f"experiments/{exp_id}/config.json"
        try:
            config = storage_handler.read_json(config_key)
            experiments.append(config)
        except FileNotFoundError:
            print(f"Warning: config.json not found for experiment {exp_id}")
        except Exception as e:
            print(f"Error reading config for {exp_id}: {e}")

    # Sort by timestamp descending (newest first)
    experiments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return experiments

@app.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    response = {}
    exp_key_prefix = f"experiments/{experiment_id}"

    try:
        # Try to load the full report first
        response = storage_handler.read_json(f"{exp_key_prefix}/report.json")
    except FileNotFoundError:
        try:
            # Fallback to config if report not ready
            response = storage_handler.read_json(f"{exp_key_prefix}/config.json")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Experiment not found")

    # Load synthetic data preview
    try:
        csv_key = f"{exp_key_prefix}/synthetic_data.csv"
        if storage_handler.file_exists(csv_key):
            df = pd.read_csv(csv_key, nrows=100)
            response["synthetic_data"] = df.head(100).to_dict(orient='records')
        else:
            response["synthetic_data"] = []
    except Exception as e:
        print(f"Could not load synthetic data preview for {experiment_id}: {e}")
        response["synthetic_data"] = []

    # Load Notes
    try:
        response["notes"] = storage_handler.read_file_content(f"{exp_key_prefix}/notes.md")
    except FileNotFoundError:
        response["notes"] = ""

    return response

@app.put("/api/experiments/{experiment_id}/notes")
def update_notes(experiment_id: str, note: NoteUpdate):
    notes_key = f"experiments/{experiment_id}/notes.md"
    storage_handler.write_file_content(notes_key, note.notes)
    
    return {"status": "success", "notes": note.notes}

@app.get("/api/experiments/{experiment_id}/download")
def download_experiment_data(experiment_id: str):
    file_path = EXPERIMENTS_DIR / experiment_id / "synthetic_data.csv"
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Dataset not found.")
    
    return FileResponse(
        path=file_path,
        filename=f"synthetic_data_{experiment_id}.csv",
        media_type='text/csv'
    )

@app.get("/api/experiments/{experiment_id}/certificate")
def generate_certificate(experiment_id: str):
    report_key = f"experiments/{experiment_id}/report.json"
    try:
        report = storage_handler.read_json(report_key)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="Experiment report not generated yet")
        
    # Create PDF in memory
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SynthLab Privacy & Compliance Audit", ln=True, align="C")
    pdf.ln(10)
    
    # Experiment Details
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Experiment ID: {report.get('experiment_id', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Date: {report.get('timestamp', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Generator Method: {report.get('method', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Privacy Budget (Epsilon): {report.get('epsilon', 'N/A')}", ln=True)
    pdf.ln(10)
    
    # Privacy Score (DCR)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "1. Privacy Validation (DCR Score)", ln=True)
    pdf.set_font("Arial", "", 12)
    
    privacy = report.get("privacy_report", {})
    dcr = privacy.get("dcr", {})
    leaked_rows = privacy.get("leaked_rows", 0)
    
    status = "PASSED" if leaked_rows == 0 else "WARNING: LEAKAGE DETECTED"
    
    pdf.set_text_color(0, 128, 0) if leaked_rows == 0 else pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 10, f"Status: {status}", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(0, 10, f"Exact Matches (Leakage): {leaked_rows}", ln=True)
    pdf.cell(0, 10, f"Min Distance to Real Record: {dcr.get('min_distance', 'N/A')}", ln=True)
    pdf.ln(10)
    
    # Signature
    pdf.ln(20)
    pdf.cell(0, 10, "_" * 50, ln=True)
    pdf.cell(0, 10, "Principal Investigator Signature", ln=True)
    
    pdf_content = pdf.output(dest='S').encode('latin1')
    
    # Save PDF to local experiments folder and return it
    cert_key = f"experiments/{experiment_id}/compliance_certificate.pdf"
    storage_handler.write_file_content(cert_key, pdf_content, 'application/pdf')
    
    return FileResponse(
        path=Path(cert_key),
        filename=f"compliance_certificate_{experiment_id}.pdf",
        media_type='application/pdf'
    )

@app.get("/api/experiments/{experiment_id}/download/fhir")
def download_experiment_fhir(experiment_id: str):
    csv_key = f"experiments/{experiment_id}/synthetic_data.csv"
    csv_path = Path(csv_key)
    if not csv_path.is_file():
        raise HTTPException(status_code=404, detail=f"Dataset not found: {csv_key}")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dataset: {e}")
        
    # Convert and get JSON content
    converter = FHIRConverter()
    fhir_json_str = converter.convert_to_patient_bundle(df)
    
    # Save FHIR JSON to local experiments folder and return it
    fhir_key = f"experiments/{experiment_id}/synthetic_data_fhir.json"
    storage_handler.write_file_content(fhir_key, fhir_json_str, 'application/json')
    
    return FileResponse(
        path=Path(fhir_key),
        filename=f"synthetic_data_fhir_{experiment_id}.json",
        media_type='application/json'
    )

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})

# --- Graph Annotation Endpoints ---
@app.get("/api/experiments/{experiment_id}/annotations")
def get_annotations(experiment_id: str):
    annotations_key = f"experiments/{experiment_id}/annotations.json"
    try:
        return storage_handler.read_json(annotations_key)
    except FileNotFoundError:
        return {"graph_annotations": []}

@app.post("/api/experiments/{experiment_id}/annotations")
def add_annotation(experiment_id: str, annotation: GraphAnnotation):
    annotations_key = f"experiments/{experiment_id}/annotations.json"
    lock = storage_handler.get_lock(annotations_key)
    with lock:
        try:
            data = storage_handler.read_json(annotations_key)
        except FileNotFoundError:
            data = {"graph_annotations": []}

        # Generate ID and timestamp
        annotation.id = str(uuid.uuid4())
        annotation.timestamp = pd.Timestamp.now().isoformat()
        data["graph_annotations"].append(annotation.dict())

        storage_handler.write_json(annotations_key, data)

    return annotation

@app.put("/api/experiments/{experiment_id}/annotations/{annotation_id}")
def update_annotation(experiment_id: str, annotation_id: str, annotation: GraphAnnotation):
    annotations_key = f"experiments/{experiment_id}/annotations.json"
    lock = storage_handler.get_lock(annotations_key)
    with lock:
        try:
            data = storage_handler.read_json(annotations_key)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Annotations not found")

        for i, ann in enumerate(data["graph_annotations"]):
            if ann["id"] == annotation_id:
                annotation.id = annotation_id
                annotation.timestamp = pd.Timestamp.now().isoformat()
                data["graph_annotations"][i] = annotation.dict()
                storage_handler.write_json(annotations_key, data)
                return annotation

        raise HTTPException(status_code=404, detail="Annotation not found")

@app.delete("/api/experiments/{experiment_id}/annotations/{annotation_id}")
def delete_annotation(experiment_id: str, annotation_id: str):
    annotations_key = f"experiments/{experiment_id}/annotations.json"
    lock = storage_handler.get_lock(annotations_key)
    with lock:
        try:
            data = storage_handler.read_json(annotations_key)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Annotations not found")

        original_len = len(data["graph_annotations"])
        data["graph_annotations"] = [a for a in data["graph_annotations"] if a["id"] != annotation_id]

        if len(data["graph_annotations"]) == original_len:
            raise HTTPException(status_code=404, detail="Annotation not found")

        storage_handler.write_json(annotations_key, data)

    return {"status": "deleted"}

# --- Literature RAG Endpoints ---
@app.post("/api/literature/upload")
async def upload_literature(files: List[UploadFile] = File(...)):
    if not LITERATURE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Literature search dependencies not installed.")
    
    session_id = f"lit_{uuid.uuid4().hex[:8]}"
    try:
        session = LiteratureSearch()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) # For missing API key

    for file in files:
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Please upload PDFs only.")
        
        contents = await file.read()
        session.add_pdf_bytes(contents, filename=file.filename)
    
    literature_sessions[session_id] = session
    stats = session.get_stats()
    
    return {"session_id": session_id, "stats": stats}

@app.post("/api/literature/search")
async def search_literature(request: LitSearchRequest):
    session_id = request.session_id
    query = request.query
    
    session = literature_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Literature session not found or expired.")
        
    results = session.search(query)
    return results

@app.get("/api/literature/sessions")
def list_literature_sessions():
    saved_sessions = []
    session_dir = LITERATURE_DIR / "sessions"
    if session_dir.exists():
        for f in session_dir.glob("*.pkl"):
            saved_sessions.append({
                "session_id": f.stem,
                "name": f.stem.replace("_", " ").title(),
                "saved_at": pd.Timestamp(f.stat().st_mtime, unit='s').isoformat()
            })
    saved_sessions.sort(key=lambda x: x["saved_at"], reverse=True)
    return saved_sessions

@app.post("/api/literature/sessions/{session_id}/save")
async def save_literature_session(session_id: str, payload: LitSessionSave):
    session = literature_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found.")
    
    session_dir = LITERATURE_DIR / "sessions"
    safe_name = "".join(c if c.isalnum() else "_" for c in payload.name)
    save_path = session_dir / f"{safe_name}.pkl"
    
    session.save_session(save_path)
    
    return {"status": "success", "name": payload.name, "path": str(save_path)}

# --- Static Files (for Production) ---
# Only mount if dist folder exists (for combined frontend+backend deployment)
# In split deployment (Netlify frontend + Render backend), dist won't exist
if Path("dist").exists():
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

# To run this API:
# uvicorn api:app --reload
