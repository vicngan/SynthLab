import pandas as pd
import re
from typing import Dict, Any

class ClinicalAnalyzer:
    """
    Analyzer for clinical data types, physiological constraints, and medical codes.
    """
    def __init__(self):
        # Common clinical variables and their typical physiological bounds
        # Used for "Smart Type" detection suggestions
        self.constraints = {
            'hba1c': {'min': 4.0, 'max': 14.0, 'distribution': 'gaussian', 'unit': '%'},
            'glucose': {'min': 0, 'max': 600, 'distribution': 'gamma', 'unit': 'mg/dL'},
            'spo2': {'min': 50, 'max': 100, 'distribution': 'beta', 'unit': '%'},
            'heart_rate': {'min': 30, 'max': 220, 'distribution': 'gaussian', 'unit': 'bpm'},
            'systolic_bp': {'min': 60, 'max': 250, 'distribution': 'gaussian', 'unit': 'mmHg'},
            'diastolic_bp': {'min': 40, 'max': 140, 'distribution': 'gaussian', 'unit': 'mmHg'},
            'bmi': {'min': 10, 'max': 60, 'distribution': 'lognorm', 'unit': 'kg/m2'},
        }
        # Regex for ICD-10 codes (Basic format: A00.0 to Z99.9)
        self.icd10_pattern = re.compile(r"^[A-Z][0-9][0-9AB](?:\.[0-9A-K]{1,4})?$")

    def analyze_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detects clinical columns and suggests constraints.
        """
        analysis = {
            "suggestions": {},
            "icd10_columns": [],
            "icd10_validity": {}
        }

        for col in df.columns:
            # 1. Smart Type Detection (Clinical Templates)
            col_lower = col.lower()
            for key, constraint in self.constraints.items():
                if key in col_lower:
                    analysis["suggestions"][col] = constraint
            
            # 2. ICD-10 Detection & Validation
            if df[col].dtype == 'object':
                sample = df[col].dropna().astype(str)
                if not sample.empty:
                    matches = sample.apply(lambda x: bool(self.icd10_pattern.match(x)))
                    if matches.mean() > 0.5: # If > 50% look like ICD-10
                        analysis["icd10_columns"].append(col)
                        analysis["icd10_validity"][col] = round(matches.mean() * 100, 2)
        
        return analysis