import pandas as pd 
import warnings
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer, TVAESynthesizer
from sdv.sequential import PARSynthesizer
from sdv.metadata import SingleTableMetadata
from sklearn.exceptions import ConvergenceWarning

class SyntheticGenerator: #generate synthetic data using SDv library

    SYNTHESIZERS = {
        'GaussianCopula': GaussianCopulaSynthesizer,
        'CTGAN': CTGANSynthesizer,
        'TVAE': TVAESynthesizer,
        'PAR': PARSynthesizer # Probabilistic AutoRegressive for sequential data
    }

    # Medical constraints for common healthcare columns
    MEDICAL_CONSTRAINTS = {
        'Age': {'min': 0, 'max': 120, 'type': 'int'},
        'Pregnancies': {'min': 0, 'max': 20, 'type': 'int'},
        'Glucose': {'min': 0, 'max': 600},
        'BloodPressure': {'min': 40, 'max': 250},
        'SkinThickness': {'min': 0, 'max': 100},
        'Insulin': {'min': 0, 'max': 900},
        'BMI': {'min': 10, 'max': 80},
        'DiabetesPedigreeFunction': {'min': 0, 'max': 3},
        'Outcome': {'min': 0, 'max': 1, 'type': 'int'}
    }


    def __init__(self, method: str = 'GaussianCopula', apply_constraints: bool = True, model_params: dict = None, epsilon: float = None, sequence_key: str = None, sequence_index: str = None):        #initialize synthesizer
        """
        Args:
            method: Synthesizer method to use for generating synthetic data. Default is 'GaussianCopula'.
            apply_constraints: Whether to apply medical constraints to the generated data. Default is True.
            model_params: A dictionary of parameters to pass to the synthesizer.
        Returns:
            None
        """
        # Suppress SDV and CTGAN warnings to clean up logs
        warnings.filterwarnings("ignore", category=FutureWarning, module="sdv")
        warnings.filterwarnings("ignore", category=FutureWarning, module="ctgan")
        warnings.filterwarnings("ignore", category=UserWarning, module="sdv")
        # Suppress multiprocessing resource tracker warnings about leaked semaphores
        warnings.filterwarnings("ignore", message=".*leaked semaphore objects.*", category=UserWarning, module="multiprocessing.resource_tracker")
        # Suppress GMM convergence warnings from sklearn, common in CTGAN
        warnings.filterwarnings("ignore", category=ConvergenceWarning, module="sklearn.mixture._base")

        if method not in self.SYNTHESIZERS:
            raise ValueError(f"Invalid method: {method}. Choose from {list(self.SYNTHESIZERS.keys())}.")

        self.method = method
        self.apply_constraints = apply_constraints
        self.model_params = model_params or {}
        self.epsilon = epsilon
        self.sequence_key = sequence_key
        self.sequence_index = sequence_index
        self.synthesizer = None
        self.metadata = None
        

    def train(self, df: pd.DataFrame) -> None: 
        #train synthesizer on cleaned data
        """
        Args:
            df: Cleaned pandas DataFrame.
        Returns:
            None
        """
        self.metadata = SingleTableMetadata()
        self.metadata.detect_from_dataframe(df) #detect metadata from DataFrame

        # Configure metadata for Sequential (PAR) models
        if self.method == 'PAR':
            if not self.sequence_key:
                raise ValueError("PAR synthesizer requires a sequence_key (e.g., PatientID) to identify sequences.")
            
            self.metadata.update_column(self.sequence_key, sdtype='id')
            self.metadata.set_sequence_key(self.sequence_key)
            
            if self.sequence_index:
                self.metadata.set_sequence_index(self.sequence_index)

        self.synthesizer = self.SYNTHESIZERS[self.method](
            metadata=self.metadata,
            **self.model_params
        ) #initialize synthesizer
        print(f"Training {self.method} synthesizer with params: {self.model_params}...")
        self.synthesizer.fit(df) #train synthesizer on DataFrame
        print(f"Synthesizer trained using {self.method} method.")   # print confirmation message    

    def _apply_constraints(self, df: pd.DataFrame) -> pd.DataFrame:
        #apply medical constraints to DataFrame
        """
        Args:
            df: pandas DataFrame.
        Returns:
            pd.DataFrame: DataFrame with medical constraints applied.
        """
        df_constrained = df.copy() #create copy of DataFrame to avoid modifying original data
        violations = 0 #initialize counter for data points that violate constraints     

        for col in df.columns:
            if col in self.MEDICAL_CONSTRAINTS:
                constraints = self.MEDICAL_CONSTRAINTS[col]
                
                #count violations before applying constraints
                if 'min' in constraints:
                    violations += (df[col] < constraints['min']).sum()
                if 'max' in constraints:
                    violations += (df[col] > constraints['max']).sum()

                #apply bounds
                if 'min' in constraints:
                    df[col] = df[col].clip(lower=constraints['min'])
                if 'max' in constraints:
                    df[col] = df[col].clip(upper=constraints['max'])

                #convert to int if necessary
                if constraints.get('type') == 'int':
                    df[col] = df[col].round().astype(int)

        if violations > 0:
            print(f"Applied medical constraints to {violations} data points.")
        
        return df


    def generate(self, count: int) -> pd.DataFrame: 
        #generate synthetic data
        """
        Args:
            count: Number of synthetic rows to generate.
        Returns:
            pd.DataFrame: Generated synthetic data as a pandas DataFrame.
        """
        if self.synthesizer is None:
            raise RuntimeError("Synthesizer has not been trained. Call train() before generate().")

        if self.method == 'PAR':
            # For PAR, count refers to the number of sequences (e.g., patients), not total rows
            print(f"Generating {count} synthetic sequences (entities) using PAR...")
            synthetic_df = self.synthesizer.sample(num_sequences=count)
        else:
            print(f"Generating {count} synthetic rows...")
            synthetic_df = self.synthesizer.sample(num_rows=count) #generate synthetic data
    
        if self.apply_constraints:
            synthetic_df = self._apply_constraints(synthetic_df) #apply medical constraints
            print(f"Applying medical constraints to synthetic data...")
            
        return synthetic_df
        
    def add_constraint(self, column: str, min_val: float = None, max_val: float = None, dtype: str = None):
        #add custom constraints to the synthesizer
        """
        Args:
            constraints: Dictionary of custom constraints to add.
            column: Column name to apply constraints to.
            min_val: Minimum value for the column.
            max_val: Maximum value for the column.
            dtypes: Data type for the column.

        Returns:
            None
        """
        if column not in self.MEDICAL_CONSTRAINTS:
            self.MEDICAL_CONSTRAINTS[column] = {} # Initialize if it's a new constraint
        
        if min_val is not None:
            self.MEDICAL_CONSTRAINTS[column]['min'] = min_val # Update the minimum value for the column
        if max_val is not None:   
            self.MEDICAL_CONSTRAINTS[column]['max'] = max_val # Update the maximum value for the column
        if dtype is not None:
            self.MEDICAL_CONSTRAINTS[column]['type'] = dtype # Update the data type for the column

        print(f"Added/Updated custom constraints for column {column}: {self.MEDICAL_CONSTRAINTS[column]}") # Print confirmation message
