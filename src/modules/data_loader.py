from pathlib import Path
import pandas as pd
from typing import Tuple, List

class DataLoader: #loads and clean CSV data for synthetic data generation
    def __init__(self):
        pass

    def load_data(self, filepath: str) -> pd.DataFrame: #load data from CSV file
        """
        Args:
            filepath: Path to the CSV file.
        Returns:
            pd.DataFrame: Loaded data as a pandas DataFrame.
        
        """
        
        try:
            df = pd.read_csv(filepath) #read CSV file into DataFrame
            print(f"Loaded {len(df)}rows, {len(df.columns)} columns")
            return df 
        except FileNotFoundError: 
            raise FileNotFoundError(f"File not found: {filepath}")  
        
    def clean_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]: 
        #clean data by handling missing values and identifying categorical columns
        """
        Args:
            df: Input pandas DataFrame.
        Returns:
            Tuple[pd.DataFrame, List[str]]: Cleaned DataFrame and list of categorical columns.
        """
        #remove duplicates 
        df_clean = df.drop_duplicates() 

        #fill missing numeric values with median 
        numeric_cols = df_clean.select_dtypes(include=['number']).columns
        
        for col in numeric_cols: #iterate through numeric columns
            if df_clean[col].isnull().any(): #check for missing values
                df_clean[col]= df_clean[col].fillna(df_clean[col].median()) #fill missing values with median

        print(f"Cleaned: {len(df)} -> {len(df_clean)} rows") #print number of rows before and after cleaning
        return df_clean, df_clean.columns.tolist() #identify categorical columns
        
        


    