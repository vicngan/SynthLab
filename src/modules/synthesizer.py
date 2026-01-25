import pandas as pd 
import warnings
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer, TVAESynthesizer
from sdv.sequential import PARSynthesizer
from sdv.metadata import SingleTableMetadata
from sklearn.exceptions import ConvergenceWarning

from .model_cache import ModelCache
from .constraint_manager import ConstraintManager

class SyntheticGenerator: #generate synthetic data using SDv library

    SYNTHESIZERS = {
        'GaussianCopula': GaussianCopulaSynthesizer,
        'CTGAN': CTGANSynthesizer,
        'TVAE': TVAESynthesizer,
        'PAR': PARSynthesizer # Probabilistic AutoRegressive for sequential data
    }

    def __init__(
        self,
        method: str = 'GaussianCopula',
        model_params: dict = None,
        epsilon: float = None,
        sequence_key: str = None,
        sequence_index: str = None,
        cache: ModelCache = None,
        constraint_manager: ConstraintManager = None
    ):
        """
        Args:
            method: Synthesizer method to use for generating synthetic data. Default is 'GaussianCopula'.
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
        self.model_params = model_params or {}
        self.epsilon = epsilon
        self.sequence_key = sequence_key
        self.sequence_index = sequence_index
        self.synthesizer = None
        self.metadata = None
        self.cache = cache
        self.constraint_manager = constraint_manager
        

    def train(self, df: pd.DataFrame) -> None: 
        #train synthesizer on cleaned data
        """
        Args:
            df: Cleaned pandas DataFrame.
        Returns:
            None
        """
        # --- Caching Logic ---
        cache_key = None
        if self.cache:
            # Combine model params with other relevant config for a unique key
            config_for_cache = {
                **self.model_params,
                'epsilon': self.epsilon,
                'sequence_key': self.sequence_key,
                'sequence_index': self.sequence_index
            }
            cache_key = self.cache.generate_cache_key(df, self.method, config_for_cache)

            # Try to load from cache
            cached_model = self.cache.load_model(cache_key)
            if cached_model:
                self.synthesizer = cached_model['synthesizer']
                self.metadata = cached_model['metadata']
                print(f"Loaded trained {self.method} model from cache.")
                return

        # --- If not cached, proceed with training ---
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
        print(f"Synthesizer trained using {self.method} method.")

        # --- Save to cache after training ---
        if self.cache and cache_key:
            model_to_cache = {
                'synthesizer': self.synthesizer,
                'metadata': self.metadata
            }
            self.cache.save_model(cache_key, model_to_cache)

    def _apply_constraints(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.constraint_manager:
            return self.constraint_manager.apply_constraints(df)
        print("Warning: No constraint manager provided. Skipping constraints.")
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

        synthetic_df = self._apply_constraints(synthetic_df)

        return synthetic_df
