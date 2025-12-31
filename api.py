from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO, StringIO

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport 

app = FastAPI(
    title="SynthLab API",
    description = "Generate synthetic data and evaluate its quality from CSV files.",
    version = "0.1.0"
)

@app.get("/")
def root():
    return {"message" :"SynthLab API", "docs": "/docs"}

@app.post("/generate")
async def generate_synthetic_data(
        file: UploadFile = File(...),
        rows: int = 1000,
        method: str = "GaussianCopula"
    ):

        """    
        Generate synthetic data from a CSV file using the specified method and number of rows.
            
        Args:        
            file file (UploadFile): The CSV file to be used for generating synthetic data.   
            rows (int): The number of rows in the synthetic data.
            method (str): The method used to generate synthetic data.
            
        Returns:        
            dict: A dictionary containing the synthetic data.
    
        """
        if not file.filename.endswith(".csv"):
                raise HTTPException(status_code=400, detail="Only CSV files are supported")

        if method not in ["GaussianCopula", "TVAE", "CTGAN"]:
                raise HTTPException(status_code=400, detail="Invalid method. Supported methods are 'GaussianCopula', 'TVAE', and 'CTGAN'")

        #read upload file into a pandas DataFrame
        content = await file.read()
        data = pd.read_csv(StringIO(content.decode('utf-8')))

        #clean the data
        loader = DataLoader()
        cleaned_data, cols = loader.clean_data(data)

        #generate synthetic data
        generator = SyntheticGenerator(method=method)
        generator.train(cleaned_data)
        synthetic_data = generator.generate(rows)

        #return the synthetic data as a CSV file
        output = BytesIO()
        synthetic_data.to_csv(output, index=False)
        output.seek(0)

        return StreamingResponse(
            output, 
            media_type="text/csv", 
            headers={"Content-Disposition": f"attachment; filename=synthetic_data_{file.filename}.csv"}
            )

@app.post("/analyze")
async def analyze_synthetic_data(
        file: UploadFile = File(...),
        rows: int = 1000,
        method: str = "GaussianCopula"
    ):
        """    
        Analyze the quality of synthetic data generated from a CSV file.
        
        Args:        
            file (UploadFile): The CSV file to be used for generating synthetic data.   
            method (str): The method used to generate synthetic data.
            
        Returns:        
            dict: A dictionary containing the quality report.
       """
        if not file.filename.endswith(".csv"):
                raise HTTPException(status_code=400, detail="Only CSV files are supported")

        if method not in ["GaussianCopula", "TVAE", "CTGAN"]:
                raise HTTPException(status_code=400, detail="Invalid method. Supported methods are 'GaussianCopula', 'TVAE', and 'CTGAN'")

        #read upload file into a pandas DataFrame
        content = await file.read()
        data = pd.read_csv(StringIO(content.decode('utf-8')))

        #clean the data
        loader = DataLoader()
        cleaned_data = loader.clean_data(data)

        #generate synthetic data
        generator = SyntheticGenerator(method=method)
        generator.train(cleaned_data)
        synthetic_data = generator.generate(rows=len(cleaned_data))

        #analyze the quality of synthetic data
        analyzer = QualityReport()
        report = analyzer.analyze(cleaned_data, synthetic_data)

        return {
               "filename": file.filename,
               "original_rows": len(cleaned_data),
                "synthetic_rows": len(synthetic_data),
                "method": method,
                "stats": report.compare_stats(),
                "privacy": report.check_privacy(),
        }
