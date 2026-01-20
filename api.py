import pandas as pd
import io
import sys
import json
from pathlib import Path
from typing import List
import uuid

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src directory to sys.path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport
from src.modules.literature import LiteratureSearch, LITERATURE_AVAILABLE
from src.modules.clinical import ClinicalAnalyzer

# --- FastAPI App Initialization ---
app = FastAPI(
    title="SynthLab API",
    description="API for generating privacy-safe synthetic data and performing literature analysis.",
    version="0.2.0"
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

# --- Pydantic Models ---
class NoteUpdate(BaseModel):
    notes: str

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the SynthLab API"}

@app.post("/api/synthesize")
async def synthesize_data(
    file: UploadFile = File(...),
    method: str = Form("CTGAN"),
    num_rows: int = Form(1000),
    sensitive_column: str = Form(None),
    epsilon: float = Form(0.0) # Add epsilon parameter
):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        loader = DataLoader()
        clean_df, _ = loader.clean_data(df)

        # --- Clinical Analysis ---
        clinical_analyzer = ClinicalAnalyzer()
        clinical_analysis = clinical_analyzer.analyze_columns(clean_df)

        # Pass epsilon to the generator
        generator = SyntheticGenerator(method=method, epsilon=epsilon if epsilon > 0 else None)
        generator.train(clean_df)
        synthetic_data = generator.generate(num_rows)

        quality_report = QualityReport(clean_df, synthetic_data)
        
        # --- Reports ---
        stats = quality_report.compare_stats()
        privacy_check = quality_report.check_privacy()
        ks_results = quality_report.ks_test()
        dcr = quality_report.distance_to_closest_record()
        
        fairness_results = None
        if sensitive_column and sensitive_column in synthetic_data.columns:
            # Check if column is binary for flip test
            if synthetic_data[sensitive_column].nunique() == 2:
                fairness_results = quality_report.flip_test(sensitive_column)

        # --- Plots ---
        dist_plots = quality_report.plot_distributions()
        corr_plots = quality_report.plot_correlation_heatmaps()
        dist_plots_json = {col: fig.to_json() for col, fig in dist_plots.items()}
        corr_plots_json = {
            'real': corr_plots[0].to_json(),
            'synthetic': corr_plots[1].to_json(),
            'diff': corr_plots[2].to_json()
        }

        # --- Save Experiment Artifacts ---
        experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
        exp_dir = Path("experiments") / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "experiment_id": experiment_id,
            "method": method,
            "timestamp": pd.Timestamp.now().isoformat(),
            "num_rows": num_rows,
            "sensitive_column": sensitive_column,
            "epsilon": epsilon
        }
        with open(exp_dir / "config.json", "w") as f:
            json.dump(config, f, indent=4)

        # Save full report (heavy data) separately
        full_report = {**config, "quality_report": {"column_stats": stats}, "privacy_report": {**privacy_check, "dcr": dcr}, "fairness_report": fairness_results, "plots": {"distributions": dist_plots_json, "correlations": corr_plots_json}}
        with open(exp_dir / "report.json", "w") as f:
            json.dump(full_report, f, indent=4)
        
        return {
            "experiment_id": experiment_id,
            "synthetic_data": synthetic_data.to_dict(orient='records'),
            "clinical_report": clinical_analysis,
            "quality_report": {"column_stats": stats},
            "privacy_report": {**privacy_check, "dcr": dcr},
            "statistical_similarity": {"ks_test": ks_results},
            "fairness_report": fairness_results,
            "plots": {
                "distributions": dist_plots_json,
                "correlations": corr_plots_json
            }
        }

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
