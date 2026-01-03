"""
Differential Privacy Engine for SynthLab

This module implements epsilon-delta differential privacy (DP) to provide formal
privacy guarantees for synthetic data generation.

## What is Differential Privacy?

Differential Privacy is a mathematical framework that provides provable privacy
guarantees. It ensures that the presence or absence of any single individual's
data in a dataset does not significantly affect the output of a computation.

## Key Concepts:

### 1. Epsilon (ε) - Privacy Budget
- Measures privacy loss: smaller ε = stronger privacy
- ε = 0.1: Very strong privacy (high noise, lower utility)
- ε = 1.0: Balanced (recommended for most use cases)
- ε = 10.0: Weak privacy (low noise, higher utility)

### 2. Delta (δ) - Failure Probability
- Probability that privacy guarantee fails
- Typically set to 1/n² where n = dataset size
- Example: For 1000 rows, δ = 1/1,000,000 = 1e-6

### 3. How It Works:
The DP guarantee states: For any two datasets D1 and D2 that differ by one person,
the probability of getting the same output O satisfies:

    P[M(D1) = O] ≤ e^ε × P[M(D2) = O] + δ

Where M is the mechanism (our synthetic data generator).

## Implementation Approach:

We apply DP in two ways:
1. **Input Perturbation**: Add calibrated noise to the real data before training
2. **Gradient Perturbation**: Clip and add noise to gradients during CTGAN/TVAE training

This is based on:
- Abadi et al. "Deep Learning with Differential Privacy" (2016)
- Xu et al. "Modeling Tabular data using Conditional GAN" (2019)
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
import json
from datetime import datetime
from pathlib import Path


class DifferentialPrivacyEngine:
    """
    Manages epsilon-delta differential privacy for synthetic data generation.

    This engine tracks privacy budgets, calibrates noise, and provides
    privacy accounting across multiple data generation operations.

    Attributes:
        epsilon (float): Privacy budget parameter
        delta (float): Failure probability
        sensitivity (float): Maximum change one record can cause
        noise_mechanism (str): 'laplace' or 'gaussian'
        budget_used (float): Cumulative epsilon spent
        operations (list): Log of all DP operations
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        noise_mechanism: str = 'gaussian'
    ):
        """
        Initialize the Differential Privacy Engine.

        Args:
            epsilon: Privacy budget (0.01 to 10.0). Lower = more privacy.
            delta: Failure probability. Should be << 1/dataset_size.
            noise_mechanism: 'laplace' for pure DP, 'gaussian' for (ε,δ)-DP.

        Raises:
            ValueError: If epsilon <= 0 or delta < 0 or delta >= 1
        """
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        if not (0 <= delta < 1):
            raise ValueError(f"Delta must be in [0, 1), got {delta}")

        self.epsilon = epsilon
        self.delta = delta
        self.noise_mechanism = noise_mechanism
        self.budget_used = 0.0
        self.operations = []

        print(f"✓ Initialized Differential Privacy Engine")
        print(f"  Epsilon (ε): {epsilon} - Privacy Budget")
        print(f"  Delta (δ): {delta} - Failure Probability")
        print(f"  Mechanism: {noise_mechanism.capitalize()} Noise")

    def calibrate_noise_scale(
        self,
        sensitivity: float,
        epsilon: Optional[float] = None,
        delta: Optional[float] = None
    ) -> float:
        """
        Calculate the noise scale needed for differential privacy.

        ## Mathematical Background:

        ### Laplace Mechanism (Pure ε-DP):
        For a query with sensitivity Δf, adding Laplace noise with scale b = Δf/ε
        provides ε-differential privacy.

        Laplace distribution: Lap(b) with PDF: f(x) = (1/2b) * exp(-|x|/b)

        ### Gaussian Mechanism ((ε,δ)-DP):
        For approximate DP, Gaussian noise with σ = Δf * √(2ln(1.25/δ)) / ε
        provides (ε,δ)-differential privacy.

        Gaussian distribution: N(0, σ²)

        ## Sensitivity:
        Sensitivity measures the maximum change in output when one record changes.

        For numeric data:
        - L1 sensitivity: Max absolute difference = max_value - min_value
        - L2 sensitivity: Euclidean distance

        Args:
            sensitivity: Maximum change one record can cause (Δf)
            epsilon: Override default epsilon
            delta: Override default delta (Gaussian only)

        Returns:
            noise_scale: Scale parameter for noise distribution

        Example:
            >>> engine = DifferentialPrivacyEngine(epsilon=1.0)
            >>> # For Age column with range [0, 120]
            >>> sensitivity = 120 - 0  # L1 sensitivity
            >>> noise_scale = engine.calibrate_noise_scale(sensitivity)
            >>> # noise_scale ≈ 120 / 1.0 = 120 for Laplace
        """
        eps = epsilon if epsilon is not None else self.epsilon
        dlt = delta if delta is not None else self.delta

        if self.noise_mechanism == 'laplace':
            # Laplace scale: b = Δf / ε
            noise_scale = sensitivity / eps
            print(f"  Laplace noise scale: {noise_scale:.4f}")
            print(f"    Formula: sensitivity ({sensitivity}) / epsilon ({eps})")

        elif self.noise_mechanism == 'gaussian':
            # Gaussian scale: σ = Δf * √(2ln(1.25/δ)) / ε
            noise_scale = sensitivity * np.sqrt(2 * np.log(1.25 / dlt)) / eps
            print(f"  Gaussian noise scale: {noise_scale:.4f}")
            print(f"    Formula: {sensitivity} * √(2ln(1.25/{dlt})) / {eps}")

        else:
            raise ValueError(f"Unknown noise mechanism: {self.noise_mechanism}")

        return noise_scale

    def add_noise_to_column(
        self,
        data: pd.Series,
        sensitivity: Optional[float] = None,
        epsilon_fraction: float = 1.0
    ) -> pd.Series:
        """
        Add calibrated DP noise to a single column.

        ## How Noise Protects Privacy:

        By adding random noise, we obscure individual contributions:
        - Original value: x = 45 (someone's age)
        - Noisy value: x' = 45 + Lap(b) = 45 + 3.2 = 48.2

        Even if an adversary knows all other records, they cannot determine
        if this person is 45, 46, or 43 years old with certainty.

        ## Epsilon Fraction:
        The total privacy budget (ε) is divided among operations:
        - If ε_total = 1.0 and we have 5 columns
        - Each column gets ε_col = 1.0 / 5 = 0.2
        - This is called "privacy budget allocation"

        Args:
            data: Column data (pandas Series)
            sensitivity: Override auto-calculated sensitivity
            epsilon_fraction: Fraction of total epsilon to use (0-1)

        Returns:
            noisy_data: Series with DP noise added

        Example:
            >>> ages = pd.Series([25, 30, 45, 60, 75])
            >>> noisy_ages = engine.add_noise_to_column(
            ...     ages,
            ...     epsilon_fraction=0.2  # Use 20% of budget
            ... )
            >>> # noisy_ages ≈ [27.3, 31.5, 43.8, 62.1, 74.2]
        """
        # Auto-calculate sensitivity if not provided
        if sensitivity is None:
            # L1 sensitivity = range of values
            sensitivity = float(data.max() - data.min())
            print(f"  Auto-calculated sensitivity for '{data.name}': {sensitivity:.4f}")
            print(f"    (max: {data.max()}, min: {data.min()})")

        # Calculate effective epsilon for this column
        effective_epsilon = self.epsilon * epsilon_fraction

        # Get noise scale
        noise_scale = self.calibrate_noise_scale(
            sensitivity,
            epsilon=effective_epsilon
        )

        # Generate noise
        if self.noise_mechanism == 'laplace':
            noise = np.random.laplace(0, noise_scale, size=len(data))
        else:  # gaussian
            noise = np.random.normal(0, noise_scale, size=len(data))

        # Add noise to data
        noisy_data = data + noise

        # Log the operation
        self._record_operation(
            operation_type='add_noise',
            column=data.name,
            epsilon_used=effective_epsilon,
            sensitivity=sensitivity,
            noise_scale=noise_scale
        )

        # Update budget
        self.budget_used += effective_epsilon

        print(f"  ✓ Added {self.noise_mechanism} noise to '{data.name}'")
        print(f"    Epsilon used: {effective_epsilon:.4f}")
        print(f"    Total budget used: {self.budget_used:.4f} / {self.epsilon}")

        return noisy_data

    def add_noise_to_dataframe(
        self,
        df: pd.DataFrame,
        column_sensitivities: Optional[Dict[str, float]] = None,
        auto_allocate: bool = True
    ) -> pd.DataFrame:
        """
        Add DP noise to all numeric columns in a DataFrame.

        ## Privacy Budget Allocation Strategies:

        ### 1. Uniform Allocation (auto_allocate=True):
        Each column gets equal share of epsilon:
        - ε_col = ε_total / n_columns
        - Simple, but may over-noise low-sensitivity columns

        ### 2. Sensitivity-Proportional Allocation:
        Allocate more budget to low-sensitivity columns:
        - ε_col = ε_total * (1 / sensitivity_col) / Σ(1 / sensitivity_all)
        - Better utility, but more complex

        ### 3. Manual Allocation:
        User specifies epsilon per column based on importance.

        Args:
            df: Input DataFrame
            column_sensitivities: Dict mapping column names to sensitivities
            auto_allocate: If True, divide epsilon equally among columns

        Returns:
            noisy_df: DataFrame with DP noise added to numeric columns

        Example:
            >>> df = pd.DataFrame({
            ...     'Age': [25, 30, 45],
            ...     'Income': [50000, 60000, 75000],
            ...     'Gender': ['M', 'F', 'M']  # Categorical, skipped
            ... })
            >>> noisy_df = engine.add_noise_to_dataframe(df)
            >>> # Only Age and Income are noised (numeric columns)
        """
        noisy_df = df.copy()

        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        n_cols = len(numeric_cols)

        if n_cols == 0:
            print("  ⚠ No numeric columns found, returning original DataFrame")
            return noisy_df

        print(f"\n📊 Adding DP noise to {n_cols} numeric columns")
        print(f"  Total privacy budget: ε = {self.epsilon}")

        # Calculate epsilon allocation
        if auto_allocate:
            epsilon_per_col = self.epsilon / n_cols
            print(f"  Auto-allocation: ε_col = {epsilon_per_col:.4f} per column")

        # Process each numeric column
        for col in numeric_cols:
            print(f"\n  Processing column: '{col}'")

            # Get sensitivity for this column
            if column_sensitivities and col in column_sensitivities:
                sensitivity = column_sensitivities[col]
            else:
                sensitivity = None  # Will auto-calculate

            # Add noise
            noisy_df[col] = self.add_noise_to_column(
                df[col],
                sensitivity=sensitivity,
                epsilon_fraction=(1.0 / n_cols) if auto_allocate else 1.0
            )

        print(f"\n✓ DP noise added to all numeric columns")
        print(f"  Total privacy budget used: {self.budget_used:.4f} / {self.epsilon}")

        return noisy_df

    def _record_operation(
        self,
        operation_type: str,
        column: str,
        epsilon_used: float,
        sensitivity: float,
        noise_scale: float
    ):
        """Record a DP operation for audit trail."""
        operation = {
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,
            'column': column,
            'epsilon_used': epsilon_used,
            'sensitivity': sensitivity,
            'noise_scale': noise_scale,
            'mechanism': self.noise_mechanism
        }
        self.operations.append(operation)

    def get_privacy_report(self) -> Dict:
        """
        Generate a comprehensive privacy report.

        This report can be used for:
        - HIPAA compliance documentation
        - IRB submissions
        - Privacy impact assessments

        Returns:
            report: Dict with privacy guarantees and operation log
        """
        report = {
            'privacy_guarantee': {
                'epsilon': self.epsilon,
                'delta': self.delta,
                'mechanism': self.noise_mechanism,
                'interpretation': self._interpret_epsilon()
            },
            'budget_tracking': {
                'total_budget': self.epsilon,
                'budget_used': self.budget_used,
                'budget_remaining': max(0, self.epsilon - self.budget_used),
                'utilization_percent': (self.budget_used / self.epsilon) * 100
            },
            'operations': self.operations,
            'timestamp': datetime.now().isoformat()
        }
        return report

    def _interpret_epsilon(self) -> str:
        """Provide human-readable interpretation of epsilon value."""
        if self.epsilon < 0.5:
            return "Very Strong Privacy - High noise, significant utility loss expected"
        elif self.epsilon < 1.5:
            return "Strong Privacy - Balanced noise and utility (RECOMMENDED)"
        elif self.epsilon < 5.0:
            return "Moderate Privacy - Lower noise, better utility"
        else:
            return "Weak Privacy - Minimal noise, privacy guarantees may be insufficient"

    def export_report(self, filepath: str = 'privacy_report.json'):
        """
        Export privacy report to JSON file.

        Args:
            filepath: Path to save the report
        """
        report = self.get_privacy_report()

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Privacy report exported to: {filepath}")

    def get_budget_remaining(self) -> float:
        """Check how much privacy budget remains."""
        return max(0, self.epsilon - self.budget_used)

    def reset_budget(self):
        """Reset the privacy budget (use with caution!)."""
        print(f"\n⚠ Resetting privacy budget")
        print(f"  Previous budget used: {self.budget_used:.4f}")
        self.budget_used = 0.0
        self.operations = []
        print(f"  Budget reset to: {self.epsilon}")


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("DIFFERENTIAL PRIVACY ENGINE - DEMONSTRATION")
    print("="*70)

    # Create a sample dataset
    print("\n1. Creating sample medical dataset...")
    df = pd.DataFrame({
        'Age': [25, 30, 45, 60, 75, 50, 35, 42, 55, 68],
        'Glucose': [85, 90, 120, 140, 160, 110, 95, 105, 130, 145],
        'BloodPressure': [70, 75, 80, 85, 90, 78, 72, 82, 88, 92],
        'BMI': [22.5, 24.0, 27.5, 30.0, 32.5, 26.0, 23.5, 28.0, 29.5, 31.0]
    })

    print(f"  Dataset shape: {df.shape}")
    print(f"\n  Original data (first 5 rows):")
    print(df.head())

    # Initialize DP engine
    print("\n" + "="*70)
    print("2. Initializing Differential Privacy Engine...")
    print("="*70)
    engine = DifferentialPrivacyEngine(
        epsilon=1.0,  # Balanced privacy
        delta=1e-5,   # Small failure probability
        noise_mechanism='gaussian'
    )

    # Add noise to dataset
    print("\n" + "="*70)
    print("3. Adding Differential Privacy Noise...")
    print("="*70)
    noisy_df = engine.add_noise_to_dataframe(df, auto_allocate=True)

    print(f"\n  Noisy data (first 5 rows):")
    print(noisy_df.head())

    # Compare statistics
    print("\n" + "="*70)
    print("4. Privacy vs Utility Trade-off Analysis")
    print("="*70)

    for col in df.columns:
        original_mean = df[col].mean()
        noisy_mean = noisy_df[col].mean()
        diff_percent = abs(original_mean - noisy_mean) / original_mean * 100

        print(f"\n  {col}:")
        print(f"    Original mean: {original_mean:.2f}")
        print(f"    Noisy mean:    {noisy_mean:.2f}")
        print(f"    Difference:    {diff_percent:.2f}%")

    # Generate privacy report
    print("\n" + "="*70)
    print("5. Privacy Guarantee Report")
    print("="*70)

    report = engine.get_privacy_report()
    print(f"\n  Privacy Guarantee: (ε={report['privacy_guarantee']['epsilon']}, "
          f"δ={report['privacy_guarantee']['delta']})-Differential Privacy")
    print(f"  Interpretation: {report['privacy_guarantee']['interpretation']}")
    print(f"\n  Budget Utilization: {report['budget_tracking']['utilization_percent']:.1f}%")
    print(f"  Budget Remaining: {report['budget_tracking']['budget_remaining']:.4f}")

    print("\n" + "="*70)
    print("✓ Demonstration Complete!")
    print("="*70)
