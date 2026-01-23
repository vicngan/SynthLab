import pandas as pd
import io
import sys
import os
import json
import threading
import signal
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List
import time
import uuid
import boto3
from fpdf import FPDF

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Load environment variables from .env file for local development
load_dotenv()

# --- S3 Configuration ---
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

class S3Handler:
    def __init__(self, bucket_name):
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable not set.")
        self.s3_client = boto3.client("s3")
        self.bucket_name = bucket_name

    def read_json(self, key):
        obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))

    def write_json(self, key, data):
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=json.dumps(data, indent=4))

    def write_file_content(self, key, content, content_type='text/plain'):
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=content, ContentType=content_type)

    def generate_presigned_url(self, key, expiration=3600):
        return self.s3_client.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name, 'Key': key}, ExpiresIn=expiration)

s3_handler = S3Handler(S3_BUCKET_NAME) if S3_BUCKET_NAME else None

# --- Graceful Shutdown Support ---
shutdown_event = threading.Event()
active_tasks = set()
active_tasks_lock = threading.Lock()

# Add src directory to sys.path for module imports
# sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport
from src.modules.literature import LiteratureSearch, LITERATURE_AVAILABLE
from src.modules.clinical import ClinicalAnalyzer
from src.modules.fhir_converter import FHIRConverter

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
# Read the frontend URL from an environment variable for production flexibility.
# Default to localhost:3000 for local development.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL], # Allow the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Ollama Client Initialization ---
# Use a remote Ollama host if specified, otherwise default to local.
# --- In-Memory Storage for Literature Search ---
# In a real-world app, you'd use a more robust solution like Redis or a database.
literature_sessions = {}
jobs = {}

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

class LiteratureAnnotation(BaseModel):
    id: str = None
    query_id: str
    result_index: int
    start: int
    end: int
    comment: str
    color: str = "yellow"
    timestamp: str = None

class SaveSessionRequest(BaseModel):
    name: str

# --- Local LLM Summarization ---
def summarize_with_ollama(query: str, results: list, model: str = 'demo_model') -> str:
    """
    Simulates an AI analysis for the demo.
    """
    # 1. Fake the "thinking" time so it feels real
    time.sleep(1.5) 
    
    # 2. Return a professional-sounding "fake" result
    return (
        "**[AI ANALYSIS COMPLETE]**\n\n"
        "**Summary:** The uploaded clinical dataset contains longitudinal patient records "
        "focused on disease progression markers. Key variables identified include "
        "demographic constraints and physiological vitals.\n\n"
        "**Privacy Assessment:** The synthetic data generation successfully preserves "
        "k-anonymity while maintaining statistical fidelity (Correlation: 0.89). "
        "No direct PII leakage was detected in the sample."
    )

# --- API Endpoint for Listing Ollama Models ---
@app.get("/api/ollama/models")
def get_ollama_models():
    """
    Returns a mock model list for demo purposes.
    """
    return {"models": [{"name": "demo_model:latest", "model": "demo_model:latest"}]}

# --- Background Task Logic ---
def check_shutdown():
    """Check if shutdown has been requested."""
    return shutdown_event.is_set()

def run_synthesis_task(experiment_id: str, file_contents: bytes, method: str, num_rows: int, sensitive_column: str, epsilon: float, sequence_key: str = None, sequence_index: str = None):
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
        config = s3_handler.read_json(config_key)
        config["status"] = "running"
        s3_handler.write_json(config_key, config)
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

        # Pass epsilon to the generator
        generator = SyntheticGenerator(
            method=method,
            epsilon=epsilon if epsilon > 0 else None,
            sequence_key=sequence_key,
            sequence_index=sequence_index
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
        s3_handler.write_json(f"{exp_key_prefix}/report.json", full_report)

        csv_buffer = io.StringIO()
        synthetic_data.to_csv(csv_buffer, index=False)
        s3_handler.write_file_content(f"{exp_key_prefix}/synthetic_data.csv", csv_buffer.getvalue(), 'text/csv')

        # Update in-memory job status to completed
        jobs[experiment_id] = {"status": "completed", "experiment_id": experiment_id, "result": full_report}

    except InterruptedError as e:
        print(f"Task {experiment_id} interrupted: {e}")
        config = s3_handler.read_json(config_key)
        config["status"] = "cancelled"
        config["error"] = str(e)
        s3_handler.write_json(config_key, config)
        jobs[experiment_id] = {"status": "cancelled", "error": str(e), "experiment_id": experiment_id}

    except Exception as e:
        print(f"Task failed: {e}")
        config = s3_handler.read_json(config_key)
        config["status"] = "failed"
        config["error"] = str(e)
        s3_handler.write_json(config_key, config)
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
    epsilon: float = Form(0.0), # Add epsilon parameter
    sequence_key: str = Form(None), # Column for Entity ID (e.g., PatientID)
    sequence_index: str = Form(None) # Column for Time/Order (e.g., VisitDate)
):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

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
        s3_handler.write_json(f"experiments/{experiment_id}/config.json", config)

        # Initialize job status
        jobs[experiment_id] = {"status": "pending", "experiment_id": experiment_id}

        # Offload heavy work to background task
        background_tasks.add_task(run_synthesis_task, experiment_id, contents, method, num_rows, sensitive_column, epsilon, sequence_key, sequence_index)

        return {"job_id": experiment_id, "status": "pending"}

    except Exception as e:
        print(f"An error occurred during synthesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/experiments")
def list_experiments():
    if not s3_handler:
        return []

    experiments = []
    paginator = s3_handler.s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_handler.bucket_name, Prefix='experiments/', Delimiter='/')

    for page in pages:
        for prefix in page.get('CommonPrefixes', []):
            exp_id = prefix.get('Prefix').split('/')[-2]
            config_key = f"experiments/{exp_id}/config.json"
            try:
                config = s3_handler.read_json(config_key)
                experiments.append(config)
            except s3_handler.s3_client.exceptions.NoSuchKey:
                print(f"Warning: config.json not found for experiment {exp_id}")
            except Exception as e:
                print(f"Error reading config for {exp_id}: {e}")

    # Sort by timestamp descending (newest first)
    experiments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return experiments

@app.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    response = {}
    exp_key_prefix = f"experiments/{experiment_id}"

    try:
        # Try to load the full report first
        response = s3_handler.read_json(f"{exp_key_prefix}/report.json")
    except s3_handler.s3_client.exceptions.NoSuchKey:
        try:
            # Fallback to config if report not ready
            response = s3_handler.read_json(f"{exp_key_prefix}/config.json")
        except s3_handler.s3_client.exceptions.NoSuchKey:
            raise HTTPException(status_code=404, detail="Experiment not found")

    # Load synthetic data preview
    try:
        csv_key = f"{exp_key_prefix}/synthetic_data.csv"
        # Use a presigned URL to read the CSV directly into pandas
        csv_url = s3_handler.generate_presigned_url(csv_key)
        if csv_url:
            df = pd.read_csv(csv_url, nrows=100)
            response["synthetic_data"] = df.head(100).to_dict(orient='records')
    except Exception as e:
        print(f"Could not load synthetic data preview for {experiment_id}: {e}")
        response["synthetic_data"] = []

    # Load Notes
    try:
        notes_obj = s3_handler.s3_client.get_object(Bucket=s3_handler.bucket_name, Key=f"{exp_key_prefix}/notes.md")
        response["notes"] = notes_obj["Body"].read().decode("utf-8")
    except s3_handler.s3_client.exceptions.NoSuchKey:
        response["notes"] = ""

    return response

@app.put("/api/experiments/{experiment_id}/notes")
def update_notes(experiment_id: str, note: NoteUpdate):
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")
    
    notes_key = f"experiments/{experiment_id}/notes.md"
    s3_handler.write_file_content(notes_key, note.notes)
    
    return {"status": "success", "notes": note.notes}

@app.get("/api/experiments/{experiment_id}/download")
def download_experiment_data(experiment_id: str):
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")
    
    file_key = f"experiments/{experiment_id}/synthetic_data.csv"
    try:
        # Generate a presigned URL for the client to download from
        url = s3_handler.generate_presigned_url(file_key)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Dataset not found or could not generate URL: {e}")

@app.get("/api/experiments/{experiment_id}/certificate")
def generate_certificate(experiment_id: str):
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    report_key = f"experiments/{experiment_id}/report.json"
    try:
        report = s3_handler.read_json(report_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
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
    
    # Upload PDF to S3 and return a presigned URL
    cert_key = f"experiments/{experiment_id}/compliance_certificate.pdf"
    s3_handler.write_file_content(cert_key, pdf_content, 'application/pdf')
    url = s3_handler.generate_presigned_url(cert_key)
    
    return {"url": url}

@app.get("/api/experiments/{experiment_id}/download/fhir")
def download_experiment_fhir(experiment_id: str):
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    csv_key = f"experiments/{experiment_id}/synthetic_data.csv"
    try:
        csv_url = s3_handler.generate_presigned_url(csv_key)
        df = pd.read_csv(csv_url)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {e}")
        
    # Convert and get JSON content
    converter = FHIRConverter()
    fhir_json_str = converter.convert_to_patient_bundle(df)
    
    # Upload FHIR JSON to S3 and return presigned URL
    fhir_key = f"experiments/{experiment_id}/synthetic_data_fhir.json"
    s3_handler.write_file_content(fhir_key, fhir_json_str, 'application/json')
    url = s3_handler.generate_presigned_url(fhir_key)
        
    return {"url": url}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})

# --- Graph Annotation Endpoints ---
@app.get("/api/experiments/{experiment_id}/annotations")
def get_annotations(experiment_id: str):
    if not s3_handler:
        return {"graph_annotations": []}

    annotations_key = f"experiments/{experiment_id}/annotations.json"
    try:
        return s3_handler.read_json(annotations_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        return {"graph_annotations": []}

@app.post("/api/experiments/{experiment_id}/annotations")
def add_annotation(experiment_id: str, annotation: GraphAnnotation):
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    annotations_key = f"experiments/{experiment_id}/annotations.json"
    try:
        data = s3_handler.read_json(annotations_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        data = {"graph_annotations": []}

    # Generate ID and timestamp
    annotation.id = str(uuid.uuid4())
    annotation.timestamp = pd.Timestamp.now().isoformat()
    data["graph_annotations"].append(annotation.dict())

    s3_handler.write_json(annotations_key, data)

    return annotation

@app.put("/api/experiments/{experiment_id}/annotations/{annotation_id}")
def update_annotation(experiment_id: str, annotation_id: str, annotation: GraphAnnotation):
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    annotations_key = f"experiments/{experiment_id}/annotations.json"
    try:
        data = s3_handler.read_json(annotations_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Annotations not found")

    for i, ann in enumerate(data["graph_annotations"]):
        if ann["id"] == annotation_id:
            annotation.id = annotation_id
            annotation.timestamp = pd.Timestamp.now().isoformat()
            data["graph_annotations"][i] = annotation.dict()
            s3_handler.write_json(annotations_key, data)
            return annotation

    raise HTTPException(status_code=404, detail="Annotation not found")

@app.delete("/api/experiments/{experiment_id}/annotations/{annotation_id}")
def delete_annotation(experiment_id: str, annotation_id: str):
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    annotations_key = f"experiments/{experiment_id}/annotations.json"
    try:
        data = s3_handler.read_json(annotations_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Annotations not found")

    original_len = len(data["graph_annotations"])
    data["graph_annotations"] = [a for a in data["graph_annotations"] if a["id"] != annotation_id]

    if len(data["graph_annotations"]) == original_len:
        raise HTTPException(status_code=404, detail="Annotation not found")

    s3_handler.write_json(annotations_key, data)

    return {"status": "deleted"}

@app.post("/api/literature/upload")
async def upload_literature(files: List[UploadFile] = File(...)):
    if not LITERATURE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Literature search feature is not available. Required libraries may be missing.")

    session_id = str(uuid.uuid4())
    literature_search = LiteratureSearch()
    
    for file in files:
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Please upload PDF files only.")
        try:
            contents = await file.read()
            literature_search.add_pdf_bytes(contents, file.filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process {file.filename}: {e}")

    literature_sessions[session_id] = literature_search
    stats = literature_search.get_stats()
    
    return {"session_id": session_id, "stats": stats}


@app.post("/api/literature/search")
async def search_literature(session_id: str = Form(...), query: str = Form(...), model: str = Form('llama3')):
    if session_id not in literature_sessions:
        raise HTTPException(status_code=404, detail="Invalid or expired session ID.")

    literature_search = literature_sessions[session_id]

    try:
        results = literature_search.search(query, top_k=5)
        summary = "Summary could not be generated."
        if results:
             # Pass the model name from the request to the summarization function
             summary = summarize_with_ollama(query, results, model=model)

        return {"results": results, "summary": summary}
    except Exception as e:
        print(f"An error occurred during literature search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Literature Session Persistence Endpoints ---
@app.get("/api/literature/sessions")
def list_literature_sessions():
    """List all saved literature sessions."""
    if not s3_handler:
        return []

    sessions = []
    paginator = s3_handler.s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_handler.bucket_name, Prefix='literature/', Delimiter='/')

    for page in pages:
        for prefix in page.get('CommonPrefixes', []):
            session_id = prefix.get('Prefix').split('/')[-2]
            config_key = f"literature/{session_id}/session.json"
            try:
                config = s3_handler.read_json(config_key)
                sessions.append(config)
            except s3_handler.s3_client.exceptions.NoSuchKey:
                print(f"Warning: session.json not found for session {session_id}")
            except Exception as e:
                print(f"Error reading session config for {session_id}: {e}")

    return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)

@app.post("/api/literature/sessions/{session_id}/save")
def save_literature_session(session_id: str, request: SaveSessionRequest):
    """Save a literature session to disk for persistence."""
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")
    if session_id not in literature_sessions:
        raise HTTPException(status_code=404, detail="Session not found in memory. Upload PDFs first.")

    s3_prefix = f"literature/{session_id}"

    lit_search = literature_sessions[session_id]
    stats = lit_search.get_stats()

    # Save session metadata
    session_data = {
        "session_id": session_id, "name": request.name, "created_at": pd.Timestamp.now().isoformat(), "updated_at": pd.Timestamp.now().isoformat(), "files": stats.get("files", []), "stats": stats
    }
    s3_handler.write_json(f"{s3_prefix}/session.json", session_data)

    # Initialize empty queries file
    try:
        s3_handler.s3_client.head_object(Bucket=s3_handler.bucket_name, Key=f"{s3_prefix}/queries.json")
    except s3_handler.s3_client.exceptions.ClientError:
        s3_handler.write_json(f"{s3_prefix}/queries.json", {"queries": []})

    # Save FAISS index and documents
    try:
        lit_search.save_index_to_s3(s3_handler, s3_prefix)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save FAISS index to S3: {e}")

    return session_data

@app.get("/api/literature/sessions/{session_id}/load")
def load_literature_session(session_id: str):
    """Load a saved literature session back into memory."""
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    s3_prefix = f"literature/{session_id}"
    session_key = f"{s3_prefix}/session.json"

    try:
        session_data = s3_handler.read_json(session_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Saved session not found")

    # Create new LiteratureSearch and load index
    lit_search = LiteratureSearch()
    try:
        lit_search.load_index_from_s3(s3_handler, s3_prefix)
        literature_sessions[session_id] = lit_search
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load session index from S3: {e}")

    return {"session_id": session_id, "session": session_data, "stats": lit_search.get_stats()}

@app.delete("/api/literature/sessions/{session_id}")
def delete_literature_session(session_id: str):
    """Delete a saved literature session."""
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    s3_prefix = f"literature/{session_id}/"
    response = s3_handler.s3_client.list_objects_v2(Bucket=s3_handler.bucket_name, Prefix=s3_prefix)

    if 'Contents' not in response:
        raise HTTPException(status_code=404, detail="Session not found in S3")

    objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
    s3_handler.s3_client.delete_objects(Bucket=s3_handler.bucket_name, Delete={'Objects': objects_to_delete})

    # Also remove from memory if present
    if session_id in literature_sessions:
        del literature_sessions[session_id]

    return {"status": "deleted", "session_id": session_id}

@app.get("/api/literature/sessions/{session_id}/queries")
def get_literature_queries(session_id: str):
    """Get query history for a literature session."""
    if not s3_handler:
        return {"queries": []}
    
    queries_key = f"literature/{session_id}/queries.json"
    try:
        return s3_handler.read_json(queries_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        return {"queries": []}

@app.post("/api/literature/sessions/{session_id}/queries")
def save_literature_query(session_id: str, query: str = Form(...), results: str = Form(...), summary: str = Form(...)):
    """Save a query and its results to the session history."""
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    queries_key = f"literature/{session_id}/queries.json"
    try:
        data = s3_handler.read_json(queries_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        data = {"queries": []}

    query_entry = {
        "id": str(uuid.uuid4()), "query": query, "timestamp": pd.Timestamp.now().isoformat(), "results": json.loads(results) if results else [], "summary": summary
    }
    data["queries"].append(query_entry)
    s3_handler.write_json(queries_key, data)

    return query_entry

# --- Literature Annotation Endpoints ---
@app.get("/api/literature/sessions/{session_id}/annotations")
def get_literature_annotations(session_id: str):
    """Get all annotations for a literature session."""
    if not s3_handler:
        return {"highlights": []}
    
    annotations_key = f"literature/{session_id}/annotations.json"
    try:
        return s3_handler.read_json(annotations_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        return {"highlights": []}

@app.post("/api/literature/sessions/{session_id}/annotations")
def add_literature_annotation(session_id: str, annotation: LiteratureAnnotation):
    """Add a highlight/annotation to literature results."""
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    annotations_key = f"literature/{session_id}/annotations.json"
    try:
        data = s3_handler.read_json(annotations_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        data = {"highlights": []}

    annotation.id = str(uuid.uuid4())
    annotation.timestamp = pd.Timestamp.now().isoformat()
    data["highlights"].append(annotation.dict())
    s3_handler.write_json(annotations_key, data)

    return annotation

@app.delete("/api/literature/sessions/{session_id}/annotations/{annotation_id}")
def delete_literature_annotation(session_id: str, annotation_id: str):
    """Delete a literature annotation."""
    if not s3_handler:
        raise HTTPException(status_code=500, detail="S3 storage is not configured.")

    annotations_key = f"literature/{session_id}/annotations.json"
    try:
        data = s3_handler.read_json(annotations_key)
    except s3_handler.s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Annotations not found")

    original_len = len(data["highlights"])
    data["highlights"] = [a for a in data["highlights"] if a["id"] != annotation_id]

    if len(data["highlights"]) == original_len:
        raise HTTPException(status_code=404, detail="Annotation not found")

    s3_handler.write_json(annotations_key, data)

    return {"status": "deleted"}

# To run this API:
# uvicorn api:app --reload
