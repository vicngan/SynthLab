import pandas as pd
import io
import sys
from pathlib import Path
from typing import List
import uuid
import os
import json
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add src directory to sys.path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport
from src.modules.literature import LiteratureSearch, LITERATURE_AVAILABLE

# --- Constants ---
EXPERIMENTS_DIR = Path("experiments")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="SynthLab API",
    description="API for generating privacy-safe synthetic data and performing literature analysis.",
    version="0.3.0" # Version bump for new feature
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
literature_sessions = {}

# --- Helper Functions ---
def save_experiment(experiment_id: str, config: dict, reports: dict, synthetic_df: pd.DataFrame):
    """Saves all artifacts for a given experiment."""
    exp_dir = EXPERIMENTS_DIR / experiment_id
    os.makedirs(exp_dir, exist_ok=True)

    # Save config
    with open(exp_dir / "config.json", 'w') as f:
        json.dump(config, f, indent=4)

    # Save reports
    with open(exp_dir / "report.json", 'w') as f:
        # Clone reports and remove raw data before saving
        reports_to_save = reports.copy()
        reports_to_save.pop("synthetic_data", None)
        json.dump(reports_to_save, f, indent=4)

    # Save synthetic data
    synthetic_df.to_csv(exp_dir / "synthetic_data.csv", index=False)


# --- API Endpoints ---
@app.on_event("startup")
async def startup_event():
    """Create experiments directory on startup."""
    os.makedirs(EXPERIMENTS_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to the SynthLab API"}

@app.post("/api/synthesize")
async def synthesize_data(
    file: UploadFile = File(...),
    method: str = Form("CTGAN"),
    num_rows: int = Form(1000),
    sensitive_column: str = Form(None),
    epsilon: float = Form(0.0),
    epochs: int = Form(300)
):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    # --- Experiment Setup ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_id = f"exp_{timestamp}_{uuid.uuid4().hex[:6]}"
    
    config = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now().isoformat(),
        "original_filename": file.filename,
        "method": method,
        "num_rows": num_rows,
        "sensitive_column": sensitive_column,
        "epochs": epochs,
        "epsilon": epsilon,
    }

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        loader = DataLoader()
        clean_df, _ = loader.clean_data(df)

        model_params = {'epochs': epochs}
        generator = SyntheticGenerator(method=method, model_params=model_params)
        generator.train(clean_df)
        synthetic_data = generator.generate(num_rows)

        quality_report = QualityReport(clean_df, synthetic_data)
        
        # --- Build Reports ---
        stats = quality_report.compare_stats()
        privacy_check = quality_report.check_privacy()
        ks_results = quality_report.ks_test()
        dcr = quality_report.distance_to_closest_record()
        
        fairness_results = None
        if sensitive_column and sensitive_column in synthetic_data.columns:
            if synthetic_data[sensitive_column].nunique() == 2:
                fairness_results = quality_report.flip_test(sensitive_column)

        dist_plots = quality_report.plot_distributions()
        corr_plots = quality_report.plot_correlation_heatmaps()
        dist_plots_json = {col: fig.to_json() for col, fig in dist_plots.items()}
        corr_plots_json = {
            'real': corr_plots[0].to_json(),
            'synthetic': corr_plots[1].to_json(),
            'diff': corr_plots[2].to_json()
        }
        
        # --- Final Response Object ---
        results = {
            "config": config,
            "synthetic_data": synthetic_data.to_dict(orient='records'),
            "quality_report": {"column_stats": stats},
            "privacy_report": {**privacy_check, "dcr": dcr},
            "statistical_similarity": {"ks_test": ks_results},
            "fairness_report": fairness_results,
            "plots": {
                "distributions": dist_plots_json,
                "correlations": corr_plots_json
            }
        }
        
        # --- Save Artifacts ---
        save_experiment(experiment_id, config, results, synthetic_data)

        return results

    except Exception as e:
        print(f"An error occurred during synthesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/experiments")
async def get_experiments():
    """Lists all saved experiments."""
    experiments = []
    if not EXPERIMENTS_DIR.exists():
        return experiments
        
    for exp_id in sorted(os.listdir(EXPERIMENTS_DIR), reverse=True):
        exp_dir = EXPERIMENTS_DIR / exp_id
        config_path = exp_dir / "config.json"
        if exp_dir.is_dir() and config_path.exists():
            with open(config_path, 'r') as f:
                try:
                    config = json.load(f)
                    experiments.append(config)
                except json.JSONDecodeError:
                    print(f"Warning: Could not read config for experiment {exp_id}")
    return experiments

@app.get("/api/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Retrieves the details for a single experiment."""
    exp_dir = EXPERIMENTS_DIR / experiment_id
    config_path = exp_dir / "config.json"
    report_path = exp_dir / "report.json"
    notes_path = exp_dir / "notes.md"

    if not exp_dir.exists() or not config_path.exists() or not report_path.exists():
        raise HTTPException(status_code=404, detail="Experiment not found.")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        notes = ""
        if notes_path.exists():
            with open(notes_path, 'r') as f:
                notes = f.read()
        
        response_data = {**config, **report, "notes": notes}

        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read experiment data: {e}")

@app.post("/api/experiments/{experiment_id}/notes")
async def save_experiment_notes(experiment_id: str, payload: dict):
    """Saves markdown notes for a given experiment."""
    exp_dir = EXPERIMENTS_DIR / experiment_id
    notes_path = exp_dir / "notes.md"
    
    if not exp_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found.")
        
    notes = payload.get("notes", "")
    
    try:
        with open(notes_path, 'w') as f:
            f.write(notes)
        return {"message": "Notes saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save notes: {e}")


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
async def search_literature(session_id: str = Form(...), query: str = Form(...)):
    if session_id not in literature_sessions:
        raise HTTPException(status_code=404, detail="Invalid or expired session ID.")

    literature_search = literature_sessions[session_id]
    
    try:
        results = literature_search.search(query, top_k=5)
        summary = "Could not generate summary."
        if results:
             summary = literature_search.summarize_results(query, results)

        return {"results": results, "summary": summary}
    except Exception as e:
        print(f"An error occurred during literature search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# To run this API:
# uvicorn api:app --reload
