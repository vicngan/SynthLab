"""
Configurable Constraint Manager for SynthLab

This module provides a flexible, template-based system for defining and applying
constraints to synthetic data generation.

## Why Constraints Matter

When generating synthetic medical data, we need to ensure:
1. **Biological Plausibility**: Age can't be negative, BMI typically 10-80
2. **Medical Validity**: Glucose levels have clinical ranges
3. **Statistical Realism**: Values should match real-world distributions
4. **Data Type Consistency**: Integers vs floats vs categories

## The Problem with Hardcoded Constraints

Previously, constraints were hardcoded in synthesizer.py:
```python
MEDICAL_CONSTRAINTS = {
    'Age': {'min': 0, 'max': 120, 'type': 'int'},
    'Glucose': {'min': 0, 'max': 600}
}
```

**Issues:**
- Can't adapt to different datasets
- No way to save/share constraint profiles
- Limited constraint types (only min/max)
- No validation or conflict detection

## The Solution: Dynamic Template System

This module provides:
1. **Multiple constraint types**: Range, categorical, statistical, custom
2. **Template library**: Pre-built profiles for common domains
3. **Conflict detection**: Validates constraints don't contradict
4. **JSON serialization**: Save/load/share profiles
5. **Extensibility**: Easy to add new constraint types

## How It Works

### Architecture:

```
User defines constraints
        ↓
ConstraintManager validates them
        ↓
Serializes to JSON (saved as template)
        ↓
Loads template when needed
        ↓
Applies constraints during synthesis
        ↓
Validates synthetic data compliance
```
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime


class Constraint:
    """
    Base class for all constraint types.

    Each constraint has:
    - column: Which column it applies to
    - constraint_type: Type of constraint
    - parameters: Constraint-specific params
    - validate(): Method to check if data satisfies constraint
    - apply(): Method to enforce constraint on data
    """

    def __init__(self, column: str, constraint_type: str, **params):
        self.column = column
        self.constraint_type = constraint_type
        self.params = params

    def validate(self, data: pd.Series) -> Dict:
        """Check if data satisfies this constraint."""
        raise NotImplementedError("Subclasses must implement validate()")

    def apply(self, data: pd.Series) -> pd.Series:
        """Enforce this constraint on data."""
        raise NotImplementedError("Subclasses must implement apply()")

    def to_dict(self) -> Dict:
        """Serialize constraint to dictionary."""
        return {
            'column': self.column,
            'constraint_type': self.constraint_type,
            'params': self.params
        }


class RangeConstraint(Constraint):
    """
    Constrains values to a numeric range [min, max].

    ## How It Works:

    1. **Validation**: Checks if all values are within [min, max]
    2. **Enforcement**: Clips values outside range

    ## Why Clipping Works:

    For synthetic data, clipping is acceptable because:
    - GAN may generate out-of-range values due to noise
    - Clipping preserves distribution shape (mostly)
    - Alternative (rejection sampling) is computationally expensive

    ## When to Use:

    - Biological constraints: Age ∈ [0, 120]
    - Medical ranges: Glucose ∈ [50, 600] mg/dL
    - Physical limits: BMI ∈ [10, 80] kg/m²

    ## Parameters:
    - min: Minimum allowed value (inclusive)
    - max: Maximum allowed value (inclusive)
    - dtype: 'int' or 'float' (optional, for type coercion)

    ## Example:
    ```python
    constraint = RangeConstraint(
        column='Age',
        min=0,
        max=120,
        dtype='int'
    )

    # Before: [25, 30, -5, 150]
    # After:  [25, 30,  0, 120]
    ```
    """

    def __init__(self, column: str, min_value: float, max_value: float,
                 dtype: Optional[str] = None, unit: Optional[str] = None):
        """
        Initialize range constraint.

        Args:
            column: Column name
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            dtype: Data type ('int' or 'float')
            unit: Unit of measurement (for documentation)
        """
        if min_value >= max_value:
            raise ValueError(f"min ({min_value}) must be < max ({max_value})")

        super().__init__(
            column,
            'range',
            min=min_value,
            max=max_value,
            dtype=dtype,
            unit=unit
        )

    def validate(self, data: pd.Series) -> Dict:
        """
        Check if data values are within range.

        Returns:
            Dict with:
            - valid: bool (True if all values in range)
            - violations: int (count of out-of-range values)
            - below_min: int (count below minimum)
            - above_max: int (count above maximum)
            - violation_percentage: float
        """
        below_min = (data < self.params['min']).sum()
        above_max = (data > self.params['max']).sum()
        violations = below_min + above_max
        total = len(data)

        return {
            'valid': violations == 0,
            'violations': int(violations),
            'below_min': int(below_min),
            'above_max': int(above_max),
            'violation_percentage': (violations / total * 100) if total > 0 else 0.0,
            'min_value': self.params['min'],
            'max_value': self.params['max']
        }

    def apply(self, data: pd.Series) -> pd.Series:
        """
        Clip values to range and optionally convert type.

        Process:
        1. Clip to [min, max]
        2. Convert to specified dtype if provided
        3. Return modified series
        """
        # Clip to range
        clipped = data.clip(lower=self.params['min'], upper=self.params['max'])

        # Convert type if specified
        if self.params['dtype'] == 'int':
            clipped = clipped.round().astype(int)
        elif self.params['dtype'] == 'float':
            clipped = clipped.astype(float)

        # Report statistics
        violations = self.validate(data)
        if violations['violations'] > 0:
            print(f"  ⚠ {self.column}: Clipped {violations['violations']} values "
                  f"({violations['violation_percentage']:.1f}%)")
            if violations['below_min'] > 0:
                print(f"    - {violations['below_min']} below {self.params['min']}")
            if violations['above_max'] > 0:
                print(f"    - {violations['above_max']} above {self.params['max']}")

        return clipped


class CategoricalConstraint(Constraint):
    """
    Constrains values to a set of allowed categories.

    ## How It Works:

    1. **Validation**: Checks if all values are in allowed set
    2. **Enforcement**: Maps invalid values to nearest valid or random valid

    ## Why This Matters:

    GANs can generate invalid categories:
    - Gender: Generates 'X' when only ['M', 'F'] exist
    - Blood Type: Generates 'Z+' when only ['A+', 'A-', 'B+', ...] exist

    ## Enforcement Strategies:

    1. **Mode replacement**: Replace with most common category
    2. **Random replacement**: Replace with random valid category
    3. **Nearest neighbor**: Replace with closest valid (for ordinal)

    ## Parameters:
    - allowed_values: List of valid categories
    - ordered: Boolean (True if ordinal, e.g., ['Low', 'Medium', 'High'])
    - replacement_strategy: 'mode', 'random', or 'nearest'

    ## Example:
    ```python
    constraint = CategoricalConstraint(
        column='BloodType',
        allowed_values=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        replacement_strategy='random'
    )

    # Before: ['A+', 'XYZ', 'B+', 'Invalid']
    # After:  ['A+', 'O+',  'B+', 'A-']  (random valid replacements)
    ```
    """

    def __init__(self, column: str, allowed_values: List[Any],
                 ordered: bool = False, replacement_strategy: str = 'random'):
        """
        Initialize categorical constraint.

        Args:
            column: Column name
            allowed_values: List of valid categories
            ordered: Whether categories have natural order
            replacement_strategy: How to replace invalid values
        """
        if not allowed_values:
            raise ValueError("allowed_values cannot be empty")

        if replacement_strategy not in ['mode', 'random', 'nearest']:
            raise ValueError(f"Invalid replacement_strategy: {replacement_strategy}")

        super().__init__(
            column,
            'categorical',
            allowed_values=allowed_values,
            ordered=ordered,
            replacement_strategy=replacement_strategy
        )

    def validate(self, data: pd.Series) -> Dict:
        """Check if all values are in allowed set."""
        allowed_set = set(self.params['allowed_values'])
        invalid_mask = ~data.isin(allowed_set)
        violations = invalid_mask.sum()
        total = len(data)

        # Get unique invalid values
        invalid_values = data[invalid_mask].unique().tolist()

        return {
            'valid': violations == 0,
            'violations': int(violations),
            'violation_percentage': (violations / total * 100) if total > 0 else 0.0,
            'invalid_values': invalid_values[:10],  # First 10 for display
            'allowed_values': self.params['allowed_values']
        }

    def apply(self, data: pd.Series) -> pd.Series:
        """Replace invalid categories with valid ones."""
        allowed_set = set(self.params['allowed_values'])
        invalid_mask = ~data.isin(allowed_set)

        if not invalid_mask.any():
            return data

        result = data.copy()
        strategy = self.params['replacement_strategy']

        if strategy == 'mode':
            # Replace with most common category
            mode_value = data[~invalid_mask].mode()[0]
            result[invalid_mask] = mode_value

        elif strategy == 'random':
            # Replace with random valid category
            n_invalid = invalid_mask.sum()
            random_values = np.random.choice(
                self.params['allowed_values'],
                size=n_invalid,
                replace=True
            )
            result[invalid_mask] = random_values

        elif strategy == 'nearest' and self.params['ordered']:
            # For ordered categories, replace with nearest valid
            # (simplified: use mode for now)
            mode_value = data[~invalid_mask].mode()[0]
            result[invalid_mask] = mode_value

        # Report
        violations = self.validate(data)
        if violations['violations'] > 0:
            print(f"  ⚠ {self.column}: Replaced {violations['violations']} invalid values "
                  f"({violations['violation_percentage']:.1f}%)")
            print(f"    Strategy: {strategy}")

        return result


class StatisticalConstraint(Constraint):
    """
    Constrains distribution to match statistical properties.

    ## How It Works:

    Instead of hard min/max, ensures distribution matches target:
    - Mean within tolerance
    - Std within tolerance
    - Optionally: skewness, kurtosis

    ## Why This Matters:

    Some variables don't have hard limits but should match population:
    - BMI: No absolute max, but should follow normal distribution
    - Lab results: Vary by individual but population has mean/std

    ## Enforcement:

    Uses **standardization and re-scaling**:
    1. Standardize: (x - mean) / std → N(0,1)
    2. Re-scale: x × target_std + target_mean → N(target_mean, target_std²)

    ## Parameters:
    - target_mean: Desired mean
    - target_std: Desired standard deviation
    - tolerance: Acceptable deviation (default 10%)

    ## Example:
    ```python
    constraint = StatisticalConstraint(
        column='BMI',
        target_mean=25.0,
        target_std=5.0,
        tolerance=0.1  # 10% tolerance
    )

    # Before: mean=30, std=10
    # After:  mean≈25, std≈5 (within 10% tolerance)
    ```
    """

    def __init__(self, column: str, target_mean: float, target_std: float,
                 tolerance: float = 0.1):
        """
        Initialize statistical constraint.

        Args:
            column: Column name
            target_mean: Desired mean
            target_std: Desired standard deviation
            tolerance: Acceptable deviation fraction (0.1 = 10%)
        """
        if target_std <= 0:
            raise ValueError("target_std must be positive")
        if not (0 < tolerance <= 1):
            raise ValueError("tolerance must be in (0, 1]")

        super().__init__(
            column,
            'statistical',
            target_mean=target_mean,
            target_std=target_std,
            tolerance=tolerance
        )

    def validate(self, data: pd.Series) -> Dict:
        """Check if distribution matches target within tolerance."""
        actual_mean = data.mean()
        actual_std = data.std()

        target_mean = self.params['target_mean']
        target_std = self.params['target_std']
        tolerance = self.params['tolerance']

        # Calculate deviations
        mean_error = abs(actual_mean - target_mean) / abs(target_mean)
        std_error = abs(actual_std - target_std) / abs(target_std)

        mean_valid = mean_error <= tolerance
        std_valid = std_error <= tolerance

        return {
            'valid': mean_valid and std_valid,
            'actual_mean': actual_mean,
            'target_mean': target_mean,
            'mean_error_pct': mean_error * 100,
            'mean_valid': mean_valid,
            'actual_std': actual_std,
            'target_std': target_std,
            'std_error_pct': std_error * 100,
            'std_valid': std_valid,
            'tolerance_pct': tolerance * 100
        }

    def apply(self, data: pd.Series) -> pd.Series:
        """Re-scale data to match target distribution."""
        # Standardize to N(0, 1)
        current_mean = data.mean()
        current_std = data.std()

        if current_std == 0:
            print(f"  ⚠ {self.column}: All values identical, cannot re-scale")
            return data

        standardized = (data - current_mean) / current_std

        # Re-scale to target distribution
        target_mean = self.params['target_mean']
        target_std = self.params['target_std']
        rescaled = standardized * target_std + target_mean

        # Report
        validation = self.validate(data)
        if not validation['valid']:
            print(f"  ℹ {self.column}: Re-scaled distribution")
            print(f"    Mean: {validation['actual_mean']:.2f} → {target_mean:.2f}")
            print(f"    Std:  {validation['actual_std']:.2f} → {target_std:.2f}")

        return rescaled


class ConstraintManager:
    """
    Manages collections of constraints with template support.

    ## Key Features:

    1. **Template Library**: Pre-built constraint profiles
    2. **Validation**: Detects conflicting constraints
    3. **Serialization**: Save/load as JSON
    4. **Application**: Apply all constraints to DataFrame
    5. **Reporting**: Generate compliance reports

    ## Usage Flow:

    ```python
    # 1. Create manager
    manager = ConstraintManager()

    # 2. Add constraints
    manager.add_constraint(RangeConstraint('Age', 0, 120, dtype='int'))
    manager.add_constraint(CategoricalConstraint('Gender', ['M', 'F']))

    # 3. Validate (checks for conflicts)
    manager.validate_constraints()

    # 4. Save as template
    manager.save_template('my_profile.json')

    # 5. Later: Load and apply
    manager2 = ConstraintManager.load_template('my_profile.json')
    constrained_df = manager2.apply_constraints(synthetic_df)
    ```
    """

    def __init__(self, name: str = "Custom Profile"):
        """Initialize constraint manager."""
        self.name = name
        self.constraints: Dict[str, List[Constraint]] = {}  # column -> [constraints]
        self.metadata = {
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'version': '1.0'
        }

    def add_constraint(self, constraint: Constraint):
        """
        Add a constraint to the manager.

        Multiple constraints can be added to the same column:
        - Example: Age must be in [0, 120] AND have mean=45
        """
        column = constraint.column
        if column not in self.constraints:
            self.constraints[column] = []

        self.constraints[column].append(constraint)
        self.metadata['modified'] = datetime.now().isoformat()

        print(f"✓ Added {constraint.constraint_type} constraint to '{column}'")

    def validate_constraints(self) -> Dict:
        """
        Check for conflicting constraints.

        Detects:
        - Multiple range constraints with conflicting bounds
        - Statistical constraints incompatible with range constraints
        - Invalid constraint combinations

        Returns:
            Dict with validation results
        """
        conflicts = []

        for column, constraints_list in self.constraints.items():
            # Check for multiple range constraints
            range_constraints = [c for c in constraints_list if isinstance(c, RangeConstraint)]
            if len(range_constraints) > 1:
                conflicts.append({
                    'column': column,
                    'issue': 'Multiple range constraints',
                    'severity': 'ERROR'
                })

            # Check for statistical + range compatibility
            has_stat = any(isinstance(c, StatisticalConstraint) for c in constraints_list)
            has_range = any(isinstance(c, RangeConstraint) for c in constraints_list)

            if has_stat and has_range:
                stat = next(c for c in constraints_list if isinstance(c, StatisticalConstraint))
                range_c = next(c for c in constraints_list if isinstance(c, RangeConstraint))

                # Check if statistical mean is within range
                if not (range_c.params['min'] <= stat.params['target_mean'] <= range_c.params['max']):
                    conflicts.append({
                        'column': column,
                        'issue': f"Statistical mean {stat.params['target_mean']} outside range "
                                f"[{range_c.params['min']}, {range_c.params['max']}]",
                        'severity': 'WARNING'
                    })

        if conflicts:
            print("\n⚠ Constraint Validation Issues:")
            for conflict in conflicts:
                print(f"  [{conflict['severity']}] {conflict['column']}: {conflict['issue']}")
        else:
            print("\n✓ All constraints validated successfully")

        return {
            'valid': len([c for c in conflicts if c['severity'] == 'ERROR']) == 0,
            'conflicts': conflicts
        }

    def apply_constraints(self, df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
        """
        Apply all constraints to a DataFrame.

        Process:
        1. For each column with constraints
        2. Apply each constraint in order
        3. Validate final compliance
        4. Report statistics

        Args:
            df: DataFrame to constrain
            verbose: Print detailed progress

        Returns:
            Constrained DataFrame
        """
        if verbose:
            print(f"\n🔧 Applying constraints from '{self.name}'...")
            print(f"  Columns with constraints: {len(self.constraints)}")

        result = df.copy()

        for column, constraints_list in self.constraints.items():
            if column not in result.columns:
                print(f"  ⚠ Column '{column}' not found in DataFrame, skipping")
                continue

            if verbose:
                print(f"\n  Processing '{column}' ({len(constraints_list)} constraints):")

            # Apply each constraint
            for constraint in constraints_list:
                result[column] = constraint.apply(result[column])

        if verbose:
            print(f"\n✓ Constraints applied to {len(self.constraints)} columns")

        return result

    def generate_compliance_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate detailed compliance report for a DataFrame.

        Returns:
            Dict mapping column -> constraint -> validation results
        """
        report = {
            'profile_name': self.name,
            'timestamp': datetime.now().isoformat(),
            'columns': {}
        }

        for column, constraints_list in self.constraints.items():
            if column not in df.columns:
                continue

            report['columns'][column] = {
                'num_constraints': len(constraints_list),
                'constraints': []
            }

            for constraint in constraints_list:
                validation = constraint.validate(df[column])
                report['columns'][column]['constraints'].append({
                    'type': constraint.constraint_type,
                    'params': constraint.params,
                    'validation': validation
                })

        return report

    def save_template(self, filepath: str):
        """
        Save constraint profile as JSON template.

        Format:
        {
          "name": "Clinical Labs",
          "metadata": {...},
          "constraints": [
            {
              "column": "Age",
              "constraint_type": "range",
              "params": {"min": 0, "max": 120, "dtype": "int"}
            },
            ...
          ]
        }
        """
        constraints_list = []
        for column, column_constraints in self.constraints.items():
            for constraint in column_constraints:
                constraints_list.append(constraint.to_dict())

        template = {
            'name': self.name,
            'metadata': self.metadata,
            'constraints': constraints_list
        }

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(template, f, indent=2)

        print(f"\n✓ Template saved to: {filepath}")
        print(f"  Constraints: {len(constraints_list)}")

    @classmethod
    def load_template(cls, filepath: str) -> 'ConstraintManager':
        """
        Load constraint profile from JSON template.

        Creates appropriate Constraint objects based on type.
        """
        with open(filepath, 'r') as f:
            template = json.load(f)

        manager = cls(name=template['name'])
        manager.metadata = template['metadata']

        for constraint_dict in template['constraints']:
            column = constraint_dict['column']
            ctype = constraint_dict['constraint_type']
            params = constraint_dict['params']

            # Create appropriate constraint object
            if ctype == 'range':
                constraint = RangeConstraint(
                    column,
                    min_value=params['min'],
                    max_value=params['max'],
                    dtype=params.get('dtype'),
                    unit=params.get('unit')
                )
            elif ctype == 'categorical':
                constraint = CategoricalConstraint(
                    column,
                    allowed_values=params['allowed_values'],
                    ordered=params.get('ordered', False),
                    replacement_strategy=params.get('replacement_strategy', 'random')
                )
            elif ctype == 'statistical':
                constraint = StatisticalConstraint(
                    column,
                    target_mean=params['target_mean'],
                    target_std=params['target_std'],
                    tolerance=params.get('tolerance', 0.1)
                )
            else:
                print(f"⚠ Unknown constraint type '{ctype}', skipping")
                continue

            manager.constraints.setdefault(column, []).append(constraint)

        print(f"\n✓ Loaded template: {manager.name}")
        print(f"  Constraints: {len(template['constraints'])}")

        return manager


# Pre-built templates
def create_clinical_labs_template() -> ConstraintManager:
    """
    Create template for clinical laboratory values.

    Based on standard clinical reference ranges.
    """
    manager = ConstraintManager(name="Clinical Labs")

    # Demographics
    manager.add_constraint(RangeConstraint('Age', 0, 120, dtype='int', unit='years'))
    manager.add_constraint(CategoricalConstraint('Gender', ['M', 'F']))

    # Vital signs
    manager.add_constraint(RangeConstraint('BloodPressure', 40, 250, unit='mm Hg'))
    manager.add_constraint(RangeConstraint('HeartRate', 30, 200, unit='bpm'))
    manager.add_constraint(RangeConstraint('Temperature', 35.0, 42.0, unit='°C'))

    # Lab values
    manager.add_constraint(RangeConstraint('Glucose', 50, 600, unit='mg/dL'))
    manager.add_constraint(RangeConstraint('Cholesterol', 100, 400, unit='mg/dL'))
    manager.add_constraint(RangeConstraint('Hemoglobin', 5, 20, unit='g/dL'))

    # Body metrics
    manager.add_constraint(RangeConstraint('BMI', 10, 80, unit='kg/m²'))
    manager.add_constraint(RangeConstraint('Weight', 20, 300, unit='kg'))
    manager.add_constraint(RangeConstraint('Height', 50, 250, unit='cm'))

    return manager


def create_demographics_template() -> ConstraintManager:
    """Create template for demographic data."""
    manager = ConstraintManager(name="Demographics")

    manager.add_constraint(RangeConstraint('Age', 0, 120, dtype='int'))
    manager.add_constraint(CategoricalConstraint('Gender', ['M', 'F', 'Other']))
    manager.add_constraint(CategoricalConstraint(
        'Race',
        ['White', 'Black', 'Asian', 'Hispanic', 'Other']
    ))
    manager.add_constraint(CategoricalConstraint(
        'MaritalStatus',
        ['Single', 'Married', 'Divorced', 'Widowed']
    ))
    manager.add_constraint(CategoricalConstraint(
        'Education',
        ['High School', 'Bachelor', 'Master', 'PhD'],
        ordered=True
    ))

    return manager


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("CONSTRAINT MANAGER - DEMONSTRATION")
    print("="*70)

    # Create sample data with violations
    print("\n1. Creating sample dataset with constraint violations...")
    df = pd.DataFrame({
        'Age': [25, 30, -5, 150, 45],  # Negative and too high
        'Gender': ['M', 'F', 'X', 'M', 'Invalid'],  # Invalid categories
        'BMI': [22, 25, 40, 28, 30],
        'Glucose': [85, 90, 1000, 120, 110]  # Too high
    })

    print(f"  Shape: {df.shape}")
    print("\n  Original data:")
    print(df)

    # Create constraint manager
    print("\n" + "="*70)
    print("2. Creating Constraint Manager with mixed constraints...")
    print("="*70)

    manager = ConstraintManager(name="Demo Profile")

    # Add various constraint types
    manager.add_constraint(RangeConstraint('Age', 0, 120, dtype='int', unit='years'))
    manager.add_constraint(CategoricalConstraint('Gender', ['M', 'F'], replacement_strategy='random'))
    manager.add_constraint(RangeConstraint('Glucose', 50, 600, unit='mg/dL'))
    manager.add_constraint(StatisticalConstraint('BMI', target_mean=25.0, target_std=5.0))

    # Validate constraints
    print("\n" + "="*70)
    print("3. Validating Constraints...")
    print("="*70)
    validation = manager.validate_constraints()

    # Apply constraints
    print("\n" + "="*70)
    print("4. Applying Constraints...")
    print("="*70)
    constrained_df = manager.apply_constraints(df)

    print("\n  Constrained data:")
    print(constrained_df)

    # Generate compliance report
    print("\n" + "="*70)
    print("5. Compliance Report...")
    print("="*70)
    report = manager.generate_compliance_report(constrained_df)

    for column, col_report in report['columns'].items():
        print(f"\n  {column}:")
        for constraint in col_report['constraints']:
            print(f"    Type: {constraint['type']}")
            validation = constraint['validation']
            if validation['valid']:
                print(f"      ✓ COMPLIANT")
            else:
                print(f"      ✗ Violations: {validation.get('violations', 'N/A')}")

    # Save template
    print("\n" + "="*70)
    print("6. Saving Template...")
    print("="*70)
    manager.save_template('data/constraint_profiles/demo_profile.json')

    # Test pre-built template
    print("\n" + "="*70)
    print("7. Loading Pre-built Template...")
    print("="*70)
    clinical_manager = create_clinical_labs_template()
    clinical_manager.save_template('data/constraint_profiles/clinical_labs.json')

    print("\n" + "="*70)
    print("✓ Demonstration Complete!")
    print("="*70)
