# Configurable Constraints System - Complete Guide

## 🎯 What Problem Does This Solve?

### The Old Way (Hardcoded Constraints)

Previously in [synthesizer.py](src/modules/synthesizer.py):

```python
MEDICAL_CONSTRAINTS = {
    'Age': {'min': 0, 'max': 120, 'type': 'int'},
    'Glucose': {'min': 0, 'max': 600},
    'BMI': {'min': 10, 'max': 80}
}
```

**Problems:**
- ❌ Only works for these specific columns
- ❌ Can't use with financial, genomic, or other datasets
- ❌ No way to save/share constraint profiles
- ❌ Limited to min/max ranges only
- ❌ No validation of constraint conflicts
- ❌ Hardcoded in source code (requires editing code)

### The New Way (Template-Based System)

```python
from src.modules.constraint_manager import ConstraintManager

# Load pre-built template
manager = ConstraintManager.load_template('clinical_labs.json')

# Or create custom constraints
manager = ConstraintManager(name="My Dataset")
manager.add_constraint(RangeConstraint('Age', 0, 120, dtype='int'))
manager.add_constraint(CategoricalConstraint('Gender', ['M', 'F', 'Other']))

# Save for reuse
manager.save_template('my_profile.json')

# Apply to any dataset
constrained_df = manager.apply_constraints(synthetic_df)
```

**Benefits:**
- ✅ Works with any dataset (medical, financial, etc.)
- ✅ Save/share constraint profiles as JSON
- ✅ Multiple constraint types (range, categorical, statistical)
- ✅ Automatic conflict detection
- ✅ No code editing needed
- ✅ Compliance reporting

---

## 🏗️ Architecture: How It Works

### Component Hierarchy

```
ConstraintManager
    ├─ manages collection of constraints
    ├─ validates for conflicts
    ├─ serializes to/from JSON
    └─ applies all constraints
          ↓
    Constraint (abstract base class)
          ├─ RangeConstraint
          ├─ CategoricalConstraint
          └─ StatisticalConstraint
```

### Key Classes Explained

#### 1. `Constraint` (Base Class)

**Purpose:** Abstract base for all constraint types

**Key methods:**
- `validate(data)` → Check if data satisfies constraint
- `apply(data)` → Enforce constraint on data
- `to_dict()` → Serialize for JSON storage

**Why abstract?** Different constraint types need different validation/enforcement logic.

#### 2. `RangeConstraint`

**Purpose:** Ensure values are within [min, max]

**How it works:**

```python
constraint = RangeConstraint('Age', 0, 120, dtype='int')

# Validation
validation = constraint.validate(df['Age'])
# Returns: {
#   'valid': False,
#   'violations': 2,
#   'below_min': 1,  # One value < 0
#   'above_max': 1   # One value > 120
# }

# Enforcement (clipping)
clipped = constraint.apply(df['Age'])
# Before: [-5, 25, 30, 150]
# After:  [0,  25, 30, 120]
```

**When to use:**
- Biological limits: Age ∈ [0, 120]
- Clinical ranges: Glucose ∈ [50, 600] mg/dL
- Physical bounds: BMI ∈ [10, 80] kg/m²

**Why clipping works:**
- GANs may generate out-of-range values due to sampling noise
- Clipping preserves most of the distribution shape
- Alternative (rejection sampling) is much slower

#### 3. `CategoricalConstraint`

**Purpose:** Ensure values are from allowed set

**How it works:**

```python
constraint = CategoricalConstraint(
    'Gender',
    allowed_values=['M', 'F'],
    replacement_strategy='random'
)

# Validation
validation = constraint.validate(df['Gender'])
# Returns: {
#   'valid': False,
#   'violations': 2,
#   'invalid_values': ['X', 'Invalid']
# }

# Enforcement (replacement)
fixed = constraint.apply(df['Gender'])
# Before: ['M', 'F', 'X', 'Invalid']
# After:  ['M', 'F', 'M', 'F']  (random valid replacements)
```

**Replacement strategies:**

1. **'random'** (default): Replace with random valid category
   ```python
   # Invalid 'X' → randomly choose from ['M', 'F'] → 'M'
   ```

2. **'mode'**: Replace with most common category
   ```python
   # If 60% are 'M', replace all invalid with 'M'
   ```

3. **'nearest'**: Replace with nearest valid (for ordered categories)
   ```python
   # Education: ['HS', 'BS', 'MS', 'PhD']
   # Invalid 'College' → nearest is 'BS'
   ```

**When to use:**
- Fixed categories: Gender, Blood Type, Marital Status
- Ordered categories: Education levels, Disease stages
- Encoded values: 0/1 for binary outcomes

#### 4. `StatisticalConstraint`

**Purpose:** Match target distribution (mean, std)

**How it works:**

```python
constraint = StatisticalConstraint(
    'BMI',
    target_mean=25.0,
    target_std=5.0,
    tolerance=0.1  # 10% tolerance
)

# Validation
validation = constraint.validate(df['BMI'])
# Returns: {
#   'valid': False,
#   'actual_mean': 30.0,
#   'target_mean': 25.0,
#   'mean_error_pct': 20.0,  # 20% off
#   'actual_std': 10.0,
#   'target_std': 5.0,
#   'std_error_pct': 100.0   # 100% off
# }

# Enforcement (re-scaling)
rescaled = constraint.apply(df['BMI'])
# Mathematical process:
# 1. Standardize: z = (x - μ_actual) / σ_actual  → N(0,1)
# 2. Re-scale:   x' = z × σ_target + μ_target   → N(μ_target, σ_target²)
```

**The math explained:**

```python
# Step 1: Standardize to N(0,1)
current_mean = 30.0
current_std = 10.0
z = (BMI - 30.0) / 10.0

# Example: BMI=40 → z=(40-30)/10 = 1.0

# Step 2: Re-scale to N(25, 5²)
target_mean = 25.0
target_std = 5.0
BMI_new = z × 5.0 + 25.0

# Example: z=1.0 → BMI_new = 1.0×5 + 25 = 30
```

**When to use:**
- Population statistics: "Average BMI should be 25±5"
- Lab test norms: "Mean glucose should be 100±20 mg/dL"
- Preserving real data distribution

**Why this matters:**
- GANs might shift the mean/std
- Statistical constraint brings it back to target
- Important for downstream analysis (regression, hypothesis testing)

---

## 🔧 ConstraintManager: The Orchestrator

### What It Does

1. **Manages collections of constraints** - Multiple constraints per column
2. **Validates for conflicts** - Detects impossible combinations
3. **Applies all constraints** - In correct order
4. **Serializes to JSON** - Save/load templates
5. **Generates reports** - Compliance documentation

### Workflow

```
1. Create Manager
      ↓
2. Add Constraints
      ↓
3. Validate (check for conflicts)
      ↓
4. Apply to DataFrame
      ↓
5. Generate Compliance Report
      ↓
6. Save Template (optional)
```

### Conflict Detection

**Example conflicts:**

```python
# Conflict 1: Multiple range constraints
manager.add_constraint(RangeConstraint('Age', 0, 120))
manager.add_constraint(RangeConstraint('Age', 10, 100))  # ← CONFLICT!
# Which one to use?

# Conflict 2: Statistical mean outside range
manager.add_constraint(RangeConstraint('BMI', 10, 80))
manager.add_constraint(StatisticalConstraint('BMI', target_mean=100, ...))
# ← CONFLICT! Mean 100 > max 80
```

**How validation works:**

```python
validation = manager.validate_constraints()

# Returns:
{
    'valid': False,
    'conflicts': [
        {
            'column': 'Age',
            'issue': 'Multiple range constraints',
            'severity': 'ERROR'
        },
        {
            'column': 'BMI',
            'issue': 'Statistical mean 100 outside range [10, 80]',
            'severity': 'WARNING'
        }
    ]
}
```

### Application Order

When multiple constraints exist for a column:

```python
# Applied in order added
manager.add_constraint(RangeConstraint('Age', 0, 120))       # 1st
manager.add_constraint(StatisticalConstraint('Age', 45, 15))  # 2nd

# Execution:
# 1. Clip to [0, 120]
# 2. Then re-scale to mean=45, std=15
```

**Why order matters:**
- Clipping changes distribution
- Statistical re-scaling should happen after clipping
- Current implementation: first-added = first-applied

---

## 📦 Template System

### JSON Format

Templates are stored as JSON files:

```json
{
  "name": "Clinical Labs",
  "metadata": {
    "created": "2024-01-15T10:30:00",
    "modified": "2024-01-15T10:30:00",
    "version": "1.0"
  },
  "constraints": [
    {
      "column": "Age",
      "constraint_type": "range",
      "params": {
        "min": 0,
        "max": 120,
        "dtype": "int",
        "unit": "years"
      }
    },
    {
      "column": "Gender",
      "constraint_type": "categorical",
      "params": {
        "allowed_values": ["M", "F"],
        "ordered": false,
        "replacement_strategy": "random"
      }
    }
  ]
}
```

### Pre-built Templates

**1. Clinical Labs** ([clinical_labs.json](data/constraint_profiles/clinical_labs.json))

```python
manager = ConstraintManager.load_template('data/constraint_profiles/clinical_labs.json')

# Includes constraints for:
# - Demographics: Age, Gender
# - Vital signs: BloodPressure, HeartRate, Temperature
# - Lab values: Glucose, Cholesterol, Hemoglobin
# - Body metrics: BMI, Weight, Height
```

**2. Demographics** (create with function)

```python
from src.modules.constraint_manager import create_demographics_template

manager = create_demographics_template()

# Includes:
# - Age, Gender, Race, MaritalStatus, Education
```

### Creating Custom Templates

```python
# Step 1: Create manager
manager = ConstraintManager(name="Genomics Study")

# Step 2: Add constraints
manager.add_constraint(RangeConstraint('Age', 18, 80))  # Adult only
manager.add_constraint(CategoricalConstraint('Ethnicity', [
    'European', 'African', 'Asian', 'Hispanic', 'Mixed'
]))
manager.add_constraint(StatisticalConstraint('BMI', 25, 5))

# Step 3: Validate
validation = manager.validate_constraints()
if not validation['valid']:
    print("⚠ Fix conflicts before saving")

# Step 4: Save template
manager.save_template('data/constraint_profiles/genomics.json')

# Step 5: Later, load and use
manager2 = ConstraintManager.load_template('genomics.json')
constrained_df = manager2.apply_constraints(synthetic_df)
```

---

## 🎓 Real-World Examples

### Example 1: Diabetes Dataset

```python
import pandas as pd
from src.modules.constraint_manager import ConstraintManager, RangeConstraint

# Load synthetic data (potentially has violations)
synthetic_df = pd.read_csv('synthetic_diabetes.csv')

# Create constraint manager
manager = ConstraintManager(name="Diabetes Study")

# Add constraints based on medical knowledge
manager.add_constraint(RangeConstraint('Pregnancies', 0, 20, dtype='int'))
manager.add_constraint(RangeConstraint('Glucose', 50, 600, unit='mg/dL'))
manager.add_constraint(RangeConstraint('BloodPressure', 40, 250, unit='mm Hg'))
manager.add_constraint(RangeConstraint('SkinThickness', 0, 100, unit='mm'))
manager.add_constraint(RangeConstraint('Insulin', 0, 900, unit='uU/mL'))
manager.add_constraint(RangeConstraint('BMI', 10, 80, unit='kg/m²'))
manager.add_constraint(RangeConstraint('DiabetesPedigreeFunction', 0, 3))
manager.add_constraint(RangeConstraint('Age', 18, 120, dtype='int'))
manager.add_constraint(RangeConstraint('Outcome', 0, 1, dtype='int'))

# Apply constraints
constrained_df = manager.apply_constraints(synthetic_df)

# Generate compliance report
report = manager.generate_compliance_report(constrained_df)

# Save template for future use
manager.save_template('diabetes_constraints.json')
```

### Example 2: Financial Dataset

```python
manager = ConstraintManager(name="Credit Risk")

# Demographic constraints
manager.add_constraint(RangeConstraint('Age', 18, 100, dtype='int'))
manager.add_constraint(CategoricalConstraint('EmploymentStatus', [
    'Employed', 'Self-Employed', 'Unemployed', 'Retired'
]))

# Financial constraints
manager.add_constraint(RangeConstraint('Income', 0, 1000000, unit='USD'))
manager.add_constraint(RangeConstraint('CreditScore', 300, 850, dtype='int'))
manager.add_constraint(RangeConstraint('LoanAmount', 0, 500000, unit='USD'))

# Statistical constraints (preserve population statistics)
manager.add_constraint(StatisticalConstraint('Income', 50000, 20000))
manager.add_constraint(StatisticalConstraint('CreditScore', 680, 80))

# Outcome
manager.add_constraint(CategoricalConstraint('DefaultStatus', ['Yes', 'No']))

# Apply and save
constrained_df = manager.apply_constraints(synthetic_df)
manager.save_template('credit_risk_constraints.json')
```

### Example 3: With Differential Privacy

**Complete privacy-preserving workflow:**

```python
from src.modules.privacy_engine import DifferentialPrivacyEngine
from src.modules.synthesizer import SyntheticGenerator
from src.modules.constraint_manager import ConstraintManager

# 1. Load original data
df = pd.read_csv('patient_data.csv')

# 2. Apply differential privacy
dp_engine = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5)
noisy_df = dp_engine.add_noise_to_dataframe(df)

# 3. Train synthesizer on noisy data
generator = SyntheticGenerator(method='CTGAN')
generator.train(noisy_df)
synthetic_df = generator.generate(1000)

# 4. Load constraint template
constraint_manager = ConstraintManager.load_template('clinical_labs.json')

# 5. Apply constraints to synthetic data
constrained_df = constraint_manager.apply_constraints(synthetic_df)

# 6. Verify compliance
report = constraint_manager.generate_compliance_report(constrained_df)

# Now you have synthetic data that:
# - Has (ε=1.0, δ=1e-5)-DP guarantee ✓
# - Satisfies all medical constraints ✓
# - Is ready to share! ✓
```

---

## 📊 Compliance Reporting

### Generate Report

```python
report = manager.generate_compliance_report(constrained_df)
```

### Report Structure

```python
{
    'profile_name': 'Clinical Labs',
    'timestamp': '2024-01-15T10:30:00',
    'columns': {
        'Age': {
            'num_constraints': 1,
            'constraints': [
                {
                    'type': 'range',
                    'params': {'min': 0, 'max': 120, 'dtype': 'int'},
                    'validation': {
                        'valid': True,
                        'violations': 0,
                        'below_min': 0,
                        'above_max': 0,
                        'violation_percentage': 0.0
                    }
                }
            ]
        },
        'Gender': {
            'num_constraints': 1,
            'constraints': [
                {
                    'type': 'categorical',
                    'params': {'allowed_values': ['M', 'F']},
                    'validation': {
                        'valid': True,
                        'violations': 0,
                        'invalid_values': []
                    }
                }
            ]
        }
    }
}
```

### Use Cases for Reports

1. **IRB Documentation:**
   ```
   "All synthetic data satisfies constraints defined in 'clinical_labs.json'
   with 100% compliance. See attached compliance_report.json."
   ```

2. **Data Sharing Agreements:**
   ```
   "Data has been validated against medical constraints.
   Compliance report available upon request."
   ```

3. **Quality Assurance:**
   ```
   "Pre-deployment check: Verify all constraints satisfied before release."
   ```

---

## 🔬 Advanced Topics

### Custom Constraint Types

You can extend the system with custom constraints:

```python
class PositiveDefiniteConstraint(Constraint):
    """Ensure correlation matrix is positive definite."""

    def validate(self, data: pd.DataFrame) -> Dict:
        corr = data.corr()
        eigenvalues = np.linalg.eigvals(corr.values)
        is_valid = all(eigenvalues > 0)

        return {
            'valid': is_valid,
            'min_eigenvalue': float(eigenvalues.min())
        }

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        # Nearest positive definite matrix projection
        # (implementation omitted for brevity)
        pass
```

### Constraint Composition

Combine constraints for complex rules:

```python
# Example: Pregnancy constraints
# If Gender='F' and Age in [15, 45], then Pregnancies valid
# Otherwise, Pregnancies must be 0

class ConditionalConstraint(Constraint):
    def __init__(self, column, condition_column, condition_fn, constraint_if_true, constraint_if_false):
        # Implementation...
        pass

# Usage:
manager.add_constraint(ConditionalConstraint(
    column='Pregnancies',
    condition_column='Gender',
    condition_fn=lambda x: x == 'F',
    constraint_if_true=RangeConstraint('Pregnancies', 0, 20),
    constraint_if_false=RangeConstraint('Pregnancies', 0, 0)  # Must be 0
))
```

### Temporal Constraints

For longitudinal data:

```python
class MonotonicConstraint(Constraint):
    """Ensure values increase over time (e.g., Age, CumulativeDose)."""

    def validate(self, data: pd.Series) -> Dict:
        is_monotonic = data.is_monotonic_increasing
        violations = (~data.diff().ge(0)).sum()

        return {
            'valid': is_monotonic,
            'violations': int(violations)
        }

    def apply(self, data: pd.Series) -> pd.Series:
        # Sort to enforce monotonicity
        return data.sort_values()
```

---

## 💡 Best Practices

### 1. Start with Pre-built Templates

```python
# Don't reinvent the wheel
manager = ConstraintManager.load_template('clinical_labs.json')

# Then customize as needed
manager.add_constraint(MyCustomConstraint(...))
```

### 2. Validate Before Saving

```python
manager = ConstraintManager(name="My Profile")
# ... add constraints ...

# Always validate!
validation = manager.validate_constraints()
if validation['valid']:
    manager.save_template('my_profile.json')
else:
    print("Fix conflicts first!")
    for conflict in validation['conflicts']:
        print(f"  {conflict}")
```

### 3. Document Your Constraints

```python
# Use descriptive names and units
manager.add_constraint(RangeConstraint(
    'Glucose',
    min_value=50,
    max_value=600,
    unit='mg/dL',  # ← Important for others to understand
))
```

### 4. Test Constraints on Real Data First

```python
# Before using on synthetic data, test on real data
real_df = pd.read_csv('real_data.csv')
constrained_real = manager.apply_constraints(real_df)

# Check: How many violations?
report = manager.generate_compliance_report(real_df)
for col, col_report in report['columns'].items():
    for constraint in col_report['constraints']:
        if not constraint['validation']['valid']:
            print(f"⚠ {col}: {constraint['validation']['violations']} violations")
            print(f"  Constraint may be too strict!")
```

### 5. Version Your Templates

```python
# Include version in filename
manager.save_template('diabetes_constraints_v1.0.json')

# Update metadata
manager.metadata['version'] = '2.0'
manager.metadata['changelog'] = 'Added Insulin constraint'
```

---

## 🔗 Integration with Existing Code

### Replacing Hardcoded Constraints in synthesizer.py

**Before:**

```python
# synthesizer.py (old way)
MEDICAL_CONSTRAINTS = {
    'Age': {'min': 0, 'max': 120, 'type': 'int'},
    # ... hardcoded ...
}

def generate(self, num_rows):
    synthetic_data = self.synthesizer.sample(num_rows)

    # Apply hardcoded constraints
    for col, constraints in MEDICAL_CONSTRAINTS.items():
        if col in synthetic_data.columns:
            synthetic_data[col] = synthetic_data[col].clip(
                lower=constraints['min'],
                upper=constraints['max']
            )
    # ...
```

**After:**

```python
# synthesizer.py (new way)
from src.modules.constraint_manager import ConstraintManager

class SyntheticGenerator:
    def __init__(self, method='CTGAN', constraint_template=None):
        # ...
        self.constraint_manager = None
        if constraint_template:
            self.constraint_manager = ConstraintManager.load_template(constraint_template)

    def generate(self, num_rows):
        synthetic_data = self.synthesizer.sample(num_rows)

        # Apply dynamic constraints
        if self.constraint_manager:
            synthetic_data = self.constraint_manager.apply_constraints(synthetic_data)

        return synthetic_data

# Usage:
generator = SyntheticGenerator(
    method='CTGAN',
    constraint_template='data/constraint_profiles/clinical_labs.json'
)
synthetic_df = generator.generate(1000)  # ← Automatically constrained!
```

---

## 📚 Complete API Reference

### ConstraintManager

```python
manager = ConstraintManager(name="Profile Name")

# Add constraints
manager.add_constraint(constraint)

# Validate
validation = manager.validate_constraints()

# Apply
constrained_df = manager.apply_constraints(df, verbose=True)

# Report
report = manager.generate_compliance_report(df)

# Save/Load
manager.save_template('path/to/template.json')
manager2 = ConstraintManager.load_template('path/to/template.json')
```

### RangeConstraint

```python
constraint = RangeConstraint(
    column='ColumnName',
    min_value=0,
    max_value=100,
    dtype='int',      # Optional: 'int' or 'float'
    unit='mg/dL'      # Optional: for documentation
)
```

### CategoricalConstraint

```python
constraint = CategoricalConstraint(
    column='ColumnName',
    allowed_values=['A', 'B', 'C'],
    ordered=False,                    # True if ordinal
    replacement_strategy='random'     # 'random', 'mode', or 'nearest'
)
```

### StatisticalConstraint

```python
constraint = StatisticalConstraint(
    column='ColumnName',
    target_mean=25.0,
    target_std=5.0,
    tolerance=0.1      # 10% tolerance
)
```

---

## 🎓 Summary: Why This System Works

### Problem → Solution

| Problem | Solution |
|---------|----------|
| Hardcoded constraints | Template-based JSON storage |
| Only min/max ranges | Multiple constraint types |
| Can't share profiles | Save/load templates |
| No conflict detection | Built-in validation |
| Manual enforcement | Automatic application |
| No compliance proof | Generate reports |

### Key Benefits

1. **Flexibility**: Works with any dataset
2. **Reusability**: Save once, use many times
3. **Collaboration**: Share templates with team
4. **Documentation**: Self-documenting JSON format
5. **Validation**: Catches conflicts before errors
6. **Compliance**: Generate proof for IRB/regulators

### When to Use Each Constraint Type

- **RangeConstraint**: Known biological/physical limits
- **CategoricalConstraint**: Fixed set of categories
- **StatisticalConstraint**: Population-level properties

All three can be combined for comprehensive data quality!

---

**Files Created:**
- [src/modules/constraint_manager.py](src/modules/constraint_manager.py)
- [data/constraint_profiles/clinical_labs.json](data/constraint_profiles/clinical_labs.json)
- [data/constraint_profiles/demo_profile.json](data/constraint_profiles/demo_profile.json)
