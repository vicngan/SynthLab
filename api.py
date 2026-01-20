import pandas as pd
import io
import sys
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add src directory to sys.path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport

# --- FastAPI App Initialization ---
app = FastAPI(
    title="SynthLab API",
    description="API for generating privacy-safe synthetic data.",
    version="0.1.0"
)

# --- CORS Middleware ---
# This allows the React frontend (running on a different port) to communicate with the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust if your React app runs on a different port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the SynthLab API"}

@app.post("/api/synthesize")
async def synthesize_data(
    file: UploadFile = File(...),
    method: str = Form("CTGAN"),
    num_rows: int = Form(1000)
):
    """
    Main endpoint to generate synthetic data.
    - Receives a CSV file, synthesizer method, and number of rows.
    - Processes the data using the core Python modules.
    - Returns a JSON response with the synthetic data and quality reports.
    """
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    try:
        # --- 1. Read and Process Data ---
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        loader = DataLoader()
        clean_df, _ = loader.clean_data(df)

        # --- 2. Generate Synthetic Data ---
        generator = SyntheticGenerator(method=method)
        generator.train(clean_df)
        synthetic_data = generator.generate(num_rows)

        # --- 3. Generate Quality & Privacy Reports ---
        quality_report = QualityReport(clean_df, synthetic_data)
        
        stats = quality_report.compare_stats()
        privacy_check = quality_report.check_privacy()
        ks_results = quality_report.ks_test()
        
        # Convert plotly figures to JSON for frontend rendering
        dist_plots = quality_report.plot_distributions()
        corr_plots = quality_report.plot_correlation_heatmaps()

        dist_plots_json = {col: fig.to_json() for col, fig in dist_plots.items()}
        corr_plots_json = {
            'real': corr_plots[0].to_json(),
            'synthetic': corr_plots[1].to_json(),
            'diff': corr_plots[2].to_json()
        }
        
        # --- 4. Format and Return Response ---
        return {
            "synthetic_data": synthetic_data.to_dict(orient='records'),
            "quality_report": {
                "column_stats": stats
            },
            "privacy_report": privacy_check,
            "statistical_similarity": {
                "ks_test": ks_results
            },
            "plots": {
                "distributions": dist_plots_json,
                "correlations": corr_plots_json
            }
        }

    except Exception as e:
        # Print the error to the console for debugging
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# To run this API:
# uvicorn api:app --reload