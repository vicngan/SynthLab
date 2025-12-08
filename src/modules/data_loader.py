from pathlib import Path
import pandas as pd
from typing import Tuple, List

class DataLoader: #loads and clean CSV data for synthetic data generation
    def __init__(self, file_path: str):
        pass

    def load_data(self, filepath: str) -> pd.DataFrame: #load data from CSV file
        """
        Args:
            filepath: Path to the CSV file.
        Returns:
            pd.DataFrame: Loaded data as a pandas DataFrame.
        
        """
        
        try:
            df = pd.read_csv(filepath)
            print(f"Loaded {len(df)}rows, {len(df.columns)} columns")
            return df 
        except FileNotFoundError: 
            raise FileNotFoundError(f"File not found: {filepath}")  
        

        
        


    