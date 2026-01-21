from fhir.resources.patient import Patient
from fhir.resources.bundle import Bundle, BundleEntry
import pandas as pd
import uuid
from datetime import datetime

class FHIRConverter:
    """
    Converts tabular synthetic data into HL7 FHIR R4 resources.
    """
    def convert_to_patient_bundle(self, df: pd.DataFrame) -> str:
        entries = []
        
        for _, row in df.iterrows():
            patient = Patient()
            patient.id = str(uuid.uuid4())
            
            # --- Map Gender ---
            # Look for columns like 'gender', 'sex'
            gender_col = next((col for col in df.columns if col.lower() in ['gender', 'sex']), None)
            if gender_col:
                val = str(row[gender_col]).lower()
                # FHIR value set for administrative-gender
                if val in ['male', 'female', 'other', 'unknown']:
                    patient.gender = val
            
            # --- Map Age to BirthDate ---
            # Since synthetic data often has 'Age', we estimate birthDate
            age_col = next((col for col in df.columns if col.lower() == 'age'), None)
            if age_col:
                try:
                    val = row[age_col]
                    if pd.notna(val):
                        age = int(val)
                        current_year = datetime.now().year
                        birth_year = current_year - age
                        # Default to Jan 1st of the calculated year
                        patient.birthDate = f"{birth_year}-01-01"
                except (ValueError, TypeError):
                    pass
            
            # --- Create Bundle Entry ---
            entry = BundleEntry()
            entry.resource = patient
            # In a transaction/batch, request info is required
            entry.request = {
                "method": "POST",
                "url": "Patient"
            }
            entries.append(entry)
            
        # Create a Transaction Bundle
        bundle = Bundle(type="transaction", entry=entries)
        return bundle.json()