import pandas as pd
import io
import sys
import json
import threading
import signal
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List
import uuid
import ollama
from fpdf import FPDF

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def summarize_with_ollama(query: str, results: list, model: str = 'llama3') -> str:
    """
    Generates a summary of search results using a local LLM with Ollama.

    Args:
        query: The user's search query.
        results: A list of search result documents.
        model: The name of the Ollama model to use for summarization.

    Returns:
        The generated summary as a string.
    """
    if not results:
        return "No results to summarize."

    context = "\n\n".join([f"Source {i+1}: {res['content']}" for i, res in enumerate(results)])
    
    system_prompt = "You are a helpful research assistant. Your task is to synthesize information from the provided search results into a concise summary that directly answers the user's query."
    
    prompt = f"""
    User Query: "{query}"

    Please use the following search results to write your summary:
    {context}

    Concise Summary:
    """

    try:
        # Using ollama.chat for better conversational control and system prompts
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
        )
        return response['message']['content']
    except ollama.ResponseError as e:
        # Handle errors from the Ollama API (e.g., model not found)
        print(f"Ollama API error: {e.error}")
        if "model" in e.error and "not found" in e.error:
             return f"Error: The model '{model}' was not found by Ollama. Please make sure you have run `ollama pull {model}`."
        return f"An error occurred with the Ollama API: {e.error}"
    except Exception as e:
        # Handle other exceptions, like connection errors from httpx
        print(f"Error connecting to Ollama or during summary generation: {e}")
        return "Failed to generate summary. Please ensure the Ollama service is running and accessible."

# --- Background Task Logic ---
def check_shutdown():
    """Check if shutdown has been requested."""
    return shutdown_event.is_set()

def run_synthesis_task(experiment_id: str, file_contents: bytes, method: str, num_rows: int, sensitive_column: str, epsilon: float, sequence_key: str = None, sequence_index: str = None):
    exp_dir = Path("experiments") / experiment_id
    config_path = exp_dir / "config.json"

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
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
            config["status"] = "running"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)

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
        with open(exp_dir / "report.json", "w") as f:
            json.dump(full_report, f, indent=4)

        synthetic_data.to_csv(exp_dir / "synthetic_data.csv", index=False)

        # Update in-memory job status to completed
        jobs[experiment_id] = {"status": "completed", "experiment_id": experiment_id, "result": full_report}

    except InterruptedError as e:
        print(f"Task {experiment_id} interrupted: {e}")
        jobs[experiment_id] = {"status": "cancelled", "error": str(e)}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
            config["status"] = "cancelled"
            config["error"] = str(e)
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)

    except Exception as e:
        print(f"Task failed: {e}")
        jobs[experiment_id] = {"status": "failed", "error": str(e)}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
            config["status"] = "failed"
            config["error"] = str(e)
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)

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

    try:
        contents = await file.read()
        
        experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
        exp_dir = Path("experiments") / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)

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
        with open(exp_dir / "config.json", "w") as f:
            json.dump(config, f, indent=4)

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
    experiments_dir = Path("experiments")
    experiments = []
    
    if not experiments_dir.exists():
        return []

    # Optimized listing: Only read config.json, skip heavy reports
    for exp_dir in experiments_dir.iterdir():
        if exp_dir.is_dir() and exp_dir.name.startswith("exp_"):
            config_path = exp_dir / "config.json"
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        experiments.append(config)
                except Exception:
                    continue
    
    # Sort by timestamp descending (newest first)
    experiments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return experiments

@app.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    exp_dir = Path("experiments") / experiment_id
    if not exp_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")

    response = {}

    # Load Report (contains config + stats)
    if (exp_dir / "report.json").exists():
        with open(exp_dir / "report.json", "r") as f:
            response = json.load(f)
    elif (exp_dir / "config.json").exists():
        # Fallback if report isn't ready yet (pending/running)
        with open(exp_dir / "config.json", "r") as f:
            response = json.load(f)

    # Load synthetic data from CSV (limit to first 100 rows for performance)
    csv_path = exp_dir / "synthetic_data.csv"
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            response["synthetic_data"] = df.head(100).to_dict(orient='records')
        except Exception:
            response["synthetic_data"] = []

    # Load Notes
    if (exp_dir / "notes.md").exists():
        with open(exp_dir / "notes.md", "r") as f:
            response["notes"] = f.read()

    return response

@app.put("/api/experiments/{experiment_id}/notes")
def update_notes(experiment_id: str, note: NoteUpdate):
    exp_dir = Path("experiments") / experiment_id
    if not exp_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    with open(exp_dir / "notes.md", "w") as f:
        f.write(note.notes)
    
    return {"status": "success", "notes": note.notes}

@app.get("/api/experiments/{experiment_id}/download")
def download_experiment_data(experiment_id: str):
    exp_dir = Path("experiments") / experiment_id
    file_path = exp_dir / "synthetic_data.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    return FileResponse(file_path, media_type='text/csv', filename=f"synthetic_data_{experiment_id}.csv")

@app.get("/api/experiments/{experiment_id}/certificate")
def generate_certificate(experiment_id: str):
    exp_dir = Path("experiments") / experiment_id
    if not exp_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    report_path = exp_dir / "report.json"
    if not report_path.exists():
        raise HTTPException(status_code=400, detail="Experiment report not generated yet")
        
    with open(report_path, "r") as f:
        report = json.load(f)
        
    # Create PDF
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
    
    output_path = exp_dir / "compliance_certificate.pdf"
    pdf.output(str(output_path))
    
    return FileResponse(output_path, media_type='application/pdf', filename=f"certificate_{experiment_id}.pdf")

@app.get("/api/experiments/{experiment_id}/download/fhir")
def download_experiment_fhir(experiment_id: str):
    exp_dir = Path("experiments") / experiment_id
    csv_path = exp_dir / "synthetic_data.csv"
    
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Load data and convert
    df = pd.read_csv(csv_path)
    converter = FHIRConverter()
    fhir_json = converter.convert_to_patient_bundle(df)
    
    output_path = exp_dir / "synthetic_data_fhir.json"
    with open(output_path, "w") as f:
        f.write(fhir_json)
        
    return FileResponse(output_path, media_type='application/json', filename=f"synthetic_data_fhir_{experiment_id}.json")

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})

# --- Graph Annotation Endpoints ---
@app.get("/api/experiments/{experiment_id}/annotations")
def get_annotations(experiment_id: str):
    exp_dir = Path("experiments") / experiment_id
    if not exp_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")

    annotations_path = exp_dir / "annotations.json"
    if not annotations_path.exists():
        return {"graph_annotations": []}

    with open(annotations_path, "r") as f:
        return json.load(f)

@app.post("/api/experiments/{experiment_id}/annotations")
def add_annotation(experiment_id: str, annotation: GraphAnnotation):
    exp_dir = Path("experiments") / experiment_id
    if not exp_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")

    annotations_path = exp_dir / "annotations.json"
    data = {"graph_annotations": []}
    if annotations_path.exists():
        with open(annotations_path, "r") as f:
            data = json.load(f)

    # Generate ID and timestamp
    annotation.id = str(uuid.uuid4())
    annotation.timestamp = pd.Timestamp.now().isoformat()
    data["graph_annotations"].append(annotation.dict())

    with open(annotations_path, "w") as f:
        json.dump(data, f, indent=4)

    return annotation

@app.put("/api/experiments/{experiment_id}/annotations/{annotation_id}")
def update_annotation(experiment_id: str, annotation_id: str, annotation: GraphAnnotation):
    exp_dir = Path("experiments") / experiment_id
    annotations_path = exp_dir / "annotations.json"

    if not annotations_path.exists():
        raise HTTPException(status_code=404, detail="Annotations not found")

    with open(annotations_path, "r") as f:
        data = json.load(f)

    for i, ann in enumerate(data["graph_annotations"]):
        if ann["id"] == annotation_id:
            annotation.id = annotation_id
            annotation.timestamp = pd.Timestamp.now().isoformat()
            data["graph_annotations"][i] = annotation.dict()
            with open(annotations_path, "w") as f:
                json.dump(data, f, indent=4)
            return annotation

    raise HTTPException(status_code=404, detail="Annotation not found")

@app.delete("/api/experiments/{experiment_id}/annotations/{annotation_id}")
def delete_annotation(experiment_id: str, annotation_id: str):
    exp_dir = Path("experiments") / experiment_id
    annotations_path = exp_dir / "annotations.json"

    if not annotations_path.exists():
        raise HTTPException(status_code=404, detail="Annotations not found")

    with open(annotations_path, "r") as f:
        data = json.load(f)

    original_len = len(data["graph_annotations"])
    data["graph_annotations"] = [a for a in data["graph_annotations"] if a["id"] != annotation_id]

    if len(data["graph_annotations"]) == original_len:
        raise HTTPException(status_code=404, detail="Annotation not found")

    with open(annotations_path, "w") as f:
        json.dump(data, f, indent=4)

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
    lit_dir = Path("literature")
    if not lit_dir.exists():
        return []

    sessions = []
    for session_dir in lit_dir.iterdir():
        if session_dir.is_dir():
            session_file = session_dir / "session.json"
            if session_file.exists():
                try:
                    with open(session_file, "r") as f:
                        sessions.append(json.load(f))
                except Exception:
                    continue

    return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)

@app.post("/api/literature/sessions/{session_id}/save")
def save_literature_session(session_id: str, request: SaveSessionRequest):
    """Save a literature session to disk for persistence."""
    if session_id not in literature_sessions:
        raise HTTPException(status_code=404, detail="Session not found in memory. Upload PDFs first.")

    lit_dir = Path("literature") / session_id
    lit_dir.mkdir(parents=True, exist_ok=True)

    lit_search = literature_sessions[session_id]
    stats = lit_search.get_stats()

    # Save session metadata
    session_data = {
        "session_id": session_id,
        "name": request.name,
        "created_at": pd.Timestamp.now().isoformat(),
        "updated_at": pd.Timestamp.now().isoformat(),
        "files": stats.get("files", []),
        "stats": stats
    }

    with open(lit_dir / "session.json", "w") as f:
        json.dump(session_data, f, indent=4)

    # Initialize empty queries file
    if not (lit_dir / "queries.json").exists():
        with open(lit_dir / "queries.json", "w") as f:
            json.dump({"queries": []}, f, indent=4)

    # Save FAISS index and documents
    try:
        lit_search.save_index(str(lit_dir))
    except Exception as e:
        print(f"Warning: Could not save FAISS index: {e}")

    return session_data

@app.get("/api/literature/sessions/{session_id}/load")
def load_literature_session(session_id: str):
    """Load a saved literature session back into memory."""
    lit_dir = Path("literature") / session_id
    if not lit_dir.exists():
        raise HTTPException(status_code=404, detail="Saved session not found")

    session_file = lit_dir / "session.json"
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session metadata not found")

    # Load session metadata
    with open(session_file, "r") as f:
        session_data = json.load(f)

    # Create new LiteratureSearch and load index
    lit_search = LiteratureSearch()
    try:
        lit_search.load_index(str(lit_dir))
        literature_sessions[session_id] = lit_search
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load session index: {e}")

    return {"session_id": session_id, "session": session_data, "stats": lit_search.get_stats()}

@app.delete("/api/literature/sessions/{session_id}")
def delete_literature_session(session_id: str):
    """Delete a saved literature session."""
    lit_dir = Path("literature") / session_id
    if not lit_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    import shutil
    shutil.rmtree(lit_dir)

    # Also remove from memory if present
    if session_id in literature_sessions:
        del literature_sessions[session_id]

    return {"status": "deleted"}

@app.get("/api/literature/sessions/{session_id}/queries")
def get_literature_queries(session_id: str):
    """Get query history for a literature session."""
    lit_dir = Path("literature") / session_id
    queries_file = lit_dir / "queries.json"

    if not queries_file.exists():
        return {"queries": []}

    with open(queries_file, "r") as f:
        return json.load(f)

@app.post("/api/literature/sessions/{session_id}/queries")
def save_literature_query(session_id: str, query: str = Form(...), results: str = Form(...), summary: str = Form(...)):
    """Save a query and its results to the session history."""
    lit_dir = Path("literature") / session_id
    lit_dir.mkdir(parents=True, exist_ok=True)

    queries_file = lit_dir / "queries.json"
    data = {"queries": []}
    if queries_file.exists():
        with open(queries_file, "r") as f:
            data = json.load(f)

    query_entry = {
        "id": str(uuid.uuid4()),
        "query": query,
        "timestamp": pd.Timestamp.now().isoformat(),
        "results": json.loads(results) if results else [],
        "summary": summary
    }
    data["queries"].append(query_entry)

    with open(queries_file, "w") as f:
        json.dump(data, f, indent=4)

    return query_entry

# --- Literature Annotation Endpoints ---
@app.get("/api/literature/sessions/{session_id}/annotations")
def get_literature_annotations(session_id: str):
    """Get all annotations for a literature session."""
    lit_dir = Path("literature") / session_id
    annotations_file = lit_dir / "annotations.json"

    if not annotations_file.exists():
        return {"highlights": []}

    with open(annotations_file, "r") as f:
        return json.load(f)

@app.post("/api/literature/sessions/{session_id}/annotations")
def add_literature_annotation(session_id: str, annotation: LiteratureAnnotation):
    """Add a highlight/annotation to literature results."""
    lit_dir = Path("literature") / session_id
    lit_dir.mkdir(parents=True, exist_ok=True)

    annotations_file = lit_dir / "annotations.json"
    data = {"highlights": []}
    if annotations_file.exists():
        with open(annotations_file, "r") as f:
            data = json.load(f)

    annotation.id = str(uuid.uuid4())
    annotation.timestamp = pd.Timestamp.now().isoformat()
    data["highlights"].append(annotation.dict())

    with open(annotations_file, "w") as f:
        json.dump(data, f, indent=4)

    return annotation

@app.delete("/api/literature/sessions/{session_id}/annotations/{annotation_id}")
def delete_literature_annotation(session_id: str, annotation_id: str):
    """Delete a literature annotation."""
    lit_dir = Path("literature") / session_id
    annotations_file = lit_dir / "annotations.json"

    if not annotations_file.exists():
        raise HTTPException(status_code=404, detail="Annotations not found")

    with open(annotations_file, "r") as f:
        data = json.load(f)

    original_len = len(data["highlights"])
    data["highlights"] = [a for a in data["highlights"] if a["id"] != annotation_id]

    if len(data["highlights"]) == original_len:
        raise HTTPException(status_code=404, detail="Annotation not found")

    with open(annotations_file, "w") as f:
        json.dump(data, f, indent=4)

    return {"status": "deleted"}

# To run this API:
# uvicorn api:app --reload
