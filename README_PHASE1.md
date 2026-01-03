# 🧬 SynthLab v0.2 - Phase 1 Enhanced Privacy

## 🎯 What's New

SynthLab now has **enterprise-grade privacy protection** with:
- ✨ **Differential Privacy** (ε,δ)-guarantees
- ✨ **k-anonymity** checking
- ✨ **l-diversity** validation
- ✨ **t-closeness** testing

**Result:** Synthetic data you can confidently share with formal privacy guarantees!

---

## 🚀 Quick Start

### Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies (if needed)
pip install scipy numpy pandas
```

### Basic Usage

```python
import pandas as pd
from src.modules.privacy_engine import DifferentialPrivacyEngine
from src.modules.reidentification import ReIdentificationAnalyzer
from src.modules.synthesizer import SyntheticGenerator

# 1. Load your data
df = pd.read_csv('patient_data.csv')

# 2. Apply differential privacy
dp_engine = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5)
noisy_df = dp_engine.add_noise_to_dataframe(df)

# 3. Generate synthetic data
generator = SyntheticGenerator(method='CTGAN')
generator.train(noisy_df)
synthetic_df = generator.generate(1000)

# 4. Verify privacy protection
analyzer = ReIdentificationAnalyzer(
    real_df=df,
    synthetic_df=synthetic_df,
    quasi_identifiers=['Age', 'Gender', 'ZipCode'],
    sensitive_attributes=['Diagnosis']
)

audit = analyzer.comprehensive_privacy_audit(k=3, l=2, t=0.2)
print(f"Risk Level: {audit['summary']['risk_level']}")
print(f"Recommendation: {audit['summary']['recommendation']}")

# 5. Export if safe
if audit['summary']['risk_level'] in ['LOW', 'MEDIUM']:
    synthetic_df.to_csv('synthetic_data_SAFE.csv', index=False)
    dp_engine.export_report('privacy_guarantee.json')
```

---

## 📚 Understanding the Privacy Layers

### Layer 1: Differential Privacy

**What it does:** Adds mathematical noise to prevent reconstruction attacks.

**Privacy guarantee:**
```
(ε=1.0, δ=1e-5)-Differential Privacy
```

**What this means:**
- Even if attacker knows all other records, they can't determine your info
- Mathematically proven protection
- HIPAA/GDPR compliant when ε ≤ 1.0

**Example:**
```python
# Original age: 45
# After DP noise: 47.3
# → Individual value obscured, but statistics preserved
```

### Layer 2: k-anonymity

**What it does:** Ensures you "hide in a crowd" of at least k people.

**Check:**
```python
k_anon = analyzer.check_k_anonymity(k=3)
# ✓ PASS: Every combination of Age+Gender+ZIP appears ≥3 times
```

**What this means:**
- If adversary knows you're "25, Male, ZIP 94101"
- They find ≥3 matching records
- Can't determine which one is you (33% confidence max)

### Layer 3: l-diversity

**What it does:** Prevents homogeneity attacks.

**Check:**
```python
l_div = analyzer.check_l_diversity(l=2)
# ✓ PASS: Each group has ≥2 different diagnoses
```

**What this prevents:**
```
Bad (homogeneous):
  Group "25, Male, 94101": [Diabetes, Diabetes, Diabetes]
  → Adversary knows: "If you're in this group, you have diabetes"

Good (diverse):
  Group "25, Male, 94101": [Diabetes, Asthma, Healthy]
  → Adversary: "Could be any of 3 diagnoses" (33% confidence)
```

### Layer 4: t-closeness

**What it does:** Prevents skewness attacks.

**Check:**
```python
t_close = analyzer.check_t_closeness(t=0.2)
# ✓ PASS: Group distributions within 20% of overall distribution
```

**What this prevents:**
```
Bad (skewed):
  Overall: 60% Healthy, 30% Diabetes, 10% Cancer
  Elderly group: 10% Healthy, 10% Diabetes, 80% Cancer
  → Adversary: "If elderly, likely has cancer"

Good (t-close):
  Elderly group: 58% Healthy, 28% Diabetes, 14% Cancer
  → Similar to overall, can't infer from demographics
```

---

## 🎚️ Parameter Guidelines

### Epsilon (ε) - Privacy Budget

| Value | Privacy | Noise | Use Case |
|-------|---------|-------|----------|
| 0.1 | Very Strong | Very High | Genetic data, SSN |
| **1.0** ⭐ | **Balanced** | **Moderate** | **Medical records** |
| 5.0 | Moderate | Low | Aggregated stats |
| 10.0 | Weak | Minimal | Public datasets |

**Recommendation:** Start with ε=1.0 for most healthcare research.

### Delta (δ) - Failure Probability

**Formula:** δ = 1/n² where n = dataset size

```python
# For 1,000 rows
delta = 1 / (1000**2) = 1e-6

# For 10,000 rows
delta = 1 / (10000**2) = 1e-8
```

### k (k-anonymity)

| Value | Privacy | Use Case |
|-------|---------|----------|
| 3 | Moderate | General research |
| **5** ⭐ | **Strong** | **Medical records** |
| 10 | Very Strong | Highly sensitive |

**Recommendation:** k=5 for PHI (Protected Health Information).

### l (l-diversity)

| Value | Privacy | Use Case |
|-------|---------|----------|
| **2** ⭐ | **Minimum** | **Most scenarios** |
| 3 | Strong | High-risk attributes |
| 5 | Very Strong | Rare diseases |

**Recommendation:** l=2 minimum, l=3 for highly sensitive attributes.

### t (t-closeness)

| Value | Closeness | Use Case |
|-------|-----------|----------|
| 0.1 | Very Strict | HIV status, salary |
| **0.2** ⭐ | **Balanced** | **Medical diagnoses** |
| 0.3 | Moderate | Demographics |

**Recommendation:** t=0.2 for most medical data.

---

## 📊 Privacy Audit Interpretation

### Risk Levels

```
✓ LOW (3/3 metrics satisfied)
  → Safe to share
  → Document privacy guarantees
  → Export with confidence

⚠ MEDIUM (2/3 metrics satisfied)
  → Review violations
  → Consider regeneration
  → May be acceptable with documentation

⛔ HIGH (1/3 metrics satisfied)
  → Regenerate with stricter parameters
  → Do not share yet

🚨 CRITICAL (0/3 metrics satisfied)
  → Do NOT share
  → Major privacy issues
  → Redesign approach
```

### Example Audit Report

```
COMPREHENSIVE PRIVACY AUDIT
════════════════════════════════════════════════════

✓ k-anonymity (k=5): SATISFIED
  - 150 equivalence classes
  - Smallest group: 5 members
  - k-anonymity score: 100%

✗ l-diversity (l=2): VIOLATED
  - 12 groups with <2 distinct diagnoses
  - l-diversity score: 92%

✓ t-closeness (t=0.2): SATISFIED
  - Max distance: 0.18
  - Avg distance: 0.09

════════════════════════════════════════════════════
RISK ASSESSMENT
════════════════════════════════════════════════════
Metrics satisfied: 2/3
Risk level: MEDIUM
Recommendation: ⚠️ Review l-diversity violations

Actions:
1. Identify 12 homogeneous groups
2. Add diverse records OR generalize attributes
3. Re-run audit
```

---

## 🔧 Advanced Usage

### Custom Sensitivity Specification

```python
# If you know exact sensitivities
dp_engine = DifferentialPrivacyEngine(epsilon=1.0)
noisy_df = dp_engine.add_noise_to_dataframe(
    df,
    column_sensitivities={
        'Age': 50,       # Custom: we know Age ∈ [25, 75]
        'Glucose': 100,  # Custom: clinical range [50, 150]
        'BMI': 20        # Custom: typical range [15, 35]
    }
)
```

### Privacy Budget Allocation

```python
# Manual allocation for different column importance
engine = DifferentialPrivacyEngine(epsilon=1.0)

# Important column: use 50% of budget
engine.add_noise_to_column(df['Outcome'], epsilon_fraction=0.5)

# Less important: use 25% each
engine.add_noise_to_column(df['Age'], epsilon_fraction=0.25)
engine.add_noise_to_column(df['BMI'], epsilon_fraction=0.25)

# Check remaining budget
print(f"Budget remaining: {engine.get_budget_remaining()}")
```

### Handling Privacy Violations

```python
audit = analyzer.comprehensive_privacy_audit(k=5, l=2, t=0.2)

# If k-anonymity fails
if not audit['k_anonymity']['satisfies_k_anonymity']:
    print("Fix: Generalize quasi-identifiers")
    print(f"Current smallest group: {audit['k_anonymity']['smallest_group_size']}")
    print(f"Target k: {k}")

    # Example fix: Generalize Age
    df['Age_Generalized'] = (df['Age'] // 10) * 10  # 25 → 20, 34 → 30

    # Regenerate and re-check
    # ...

# If l-diversity fails
if not audit['l_diversity']['satisfies_l_diversity']:
    print("Fix: Add diversity to homogeneous groups")

    # Identify violating groups
    for attr, results in audit['l_diversity']['per_attribute'].items():
        print(f"Attribute '{attr}': {results['violating_groups']} groups need diversity")

    # Example fix: Oversample rare diagnoses in synthesis
    # ...

# If t-closeness fails
if not audit['t_closeness']['satisfies_t_closeness']:
    print("Fix: Resample to match overall distribution")

    # Get target distribution
    target = df['Diagnosis'].value_counts(normalize=True)
    print(f"Target distribution: {target}")

    # Resample synthetic data to match
    resampled = synthetic_df.groupby('Diagnosis', group_keys=False).apply(
        lambda x: x.sample(int(len(synthetic_df) * target[x.name]))
    )
```

---

## 📖 Complete Documentation

1. **[DIFFERENTIAL_PRIVACY_EXPLAINED.md](DIFFERENTIAL_PRIVACY_EXPLAINED.md)**
   - Mathematical foundations
   - Epsilon and delta explained
   - Noise mechanisms (Laplace vs Gaussian)
   - Privacy budget tracking

2. **[PRIVACY_METRICS_EXPLAINED.md](PRIVACY_METRICS_EXPLAINED.md)**
   - k-anonymity, l-diversity, t-closeness
   - Attack scenarios and defenses
   - Parameter selection guidelines
   - Mathematical proofs

3. **[PHASE_1_SUMMARY.md](PHASE_1_SUMMARY.md)**
   - Step-by-step mechanism explanations
   - Real-world examples
   - Integration guide

---

## 🧪 Testing the Implementation

### Run Differential Privacy Demo

```bash
source venv/bin/activate
python src/modules/privacy_engine.py
```

**Expected output:**
```
======================================================================
DIFFERENTIAL PRIVACY ENGINE - DEMONSTRATION
======================================================================

1. Creating sample medical dataset...
  Dataset shape: (10, 4)

2. Initializing Differential Privacy Engine...
✓ Initialized Differential Privacy Engine
  Epsilon (ε): 1.0 - Privacy Budget
  Delta (δ): 1e-05 - Failure Probability
  Mechanism: Gaussian Noise

3. Adding Differential Privacy Noise...
📊 Adding DP noise to 4 numeric columns
  [Progress details...]

✓ DP noise added to all numeric columns

4. Privacy vs Utility Trade-off Analysis
  Age: Difference: 10.5%
  Glucose: Difference: 8.2%
  [...]

5. Privacy Guarantee Report
  Privacy Guarantee: (ε=1.0, δ=1e-05)-Differential Privacy
  Interpretation: Strong Privacy - Balanced
```

### Run Re-identification Analyzer Demo

```bash
python src/modules/reidentification.py
```

**Expected output:**
```
======================================================================
RE-IDENTIFICATION ANALYSIS - DEMONSTRATION
======================================================================

COMPREHENSIVE PRIVACY AUDIT
══════════════════════════════════════════

🔍 Checking k-anonymity (k=3)...
  [Results...]

🌈 Checking l-diversity (l=2)...
  [Results...]

📏 Checking t-closeness (t=0.2)...
  [Results...]

RISK ASSESSMENT
══════════════════════════════════════════
Metrics satisfied: 2/3
Risk level: MEDIUM
Recommendation: [Specific actions...]
```

---

## 🔐 Privacy Guarantees Summary

### What You Can Now Claim

**For IRB/Ethics Committees:**
> "Our synthetic dataset satisfies (ε=1.0, δ=1e-5)-Differential Privacy,
> providing mathematically proven protection against reconstruction and
> membership inference attacks. Additionally, we verify k-anonymity (k≥5),
> l-diversity (l≥2), and t-closeness (t≤0.2) to prevent linkage, homogeneity,
> and skewness attacks."

**For Data Sharing Agreements:**
> "The synthetic data generation process includes:
> 1. Differential privacy noise injection (ε=1.0)
> 2. k-anonymity verification (k≥5)
> 3. l-diversity checking (l≥2)
> 4. t-closeness validation (t≤0.2)
>
> Privacy audit reports are available upon request."

**For Publications:**
> "Synthetic data was generated using CTGAN trained on differentially private
> data (ε=1.0, δ=1e-5) and validated for k-anonymity (k=5), l-diversity (l=2),
> and t-closeness (t=0.2) to ensure privacy protection [citation to Dwork 2006,
> Machanavajjhala 2007, Li 2007]."

---

## 🎓 Learning Resources

### For Understanding DP:
- [DIFFERENTIAL_PRIVACY_EXPLAINED.md](DIFFERENTIAL_PRIVACY_EXPLAINED.md) - Our comprehensive guide
- Dwork, C. (2006). "Differential Privacy" - The foundational paper
- Harvard Privacy Tools Project - Practical tutorials

### For Understanding k/l/t:
- [PRIVACY_METRICS_EXPLAINED.md](PRIVACY_METRICS_EXPLAINED.md) - Our detailed guide
- Sweeney, L. (2002). "k-anonymity: A model for protecting privacy"
- Machanavajjhala et al. (2007). "l-diversity"
- Li et al. (2007). "t-closeness"

### Interactive Learning:
```python
# Experiment with parameters to build intuition

# Try different epsilon values
for eps in [0.1, 0.5, 1.0, 5.0, 10.0]:
    engine = DifferentialPrivacyEngine(epsilon=eps)
    noisy = engine.add_noise_to_column(df['Age'])
    print(f"ε={eps}: Noise std = {noisy.std():.1f}")

# See: smaller ε → more noise → stronger privacy
```

---

## 🚀 Next Steps (Phase 1 Continued)

Still working on:
- ✅ Differential Privacy Engine ✓ **DONE**
- ✅ Advanced Re-identification Analyzer ✓ **DONE**
- 🔄 Configurable Constraints System (in progress)
- ⏳ Multi-format Data Loading
- ⏳ Model Caching
- ⏳ API Authentication
- ⏳ UI Integration

Stay tuned for more enhancements!

---

## 💡 Quick Tips

1. **Start with recommended parameters:**
   - ε=1.0, δ=1e-5, k=5, l=2, t=0.2

2. **Always run the comprehensive audit:**
   - Don't skip any of the 4 layers
   - Each catches different attack types

3. **Export privacy reports:**
   - `dp_engine.export_report('privacy.json')`
   - Include in data sharing documentation

4. **If audit fails:**
   - Don't ignore violations
   - Regenerate or adjust parameters
   - Document any trade-offs

5. **Test with small datasets first:**
   - Understand behavior before production use
   - Verify utility loss is acceptable

---

## 📞 Questions?

Refer to the detailed documentation:
- [DIFFERENTIAL_PRIVACY_EXPLAINED.md](DIFFERENTIAL_PRIVACY_EXPLAINED.md)
- [PRIVACY_METRICS_EXPLAINED.md](PRIVACY_METRICS_EXPLAINED.md)
- [PHASE_1_SUMMARY.md](PHASE_1_SUMMARY.md)

Or check the inline documentation in the source code:
- [src/modules/privacy_engine.py](src/modules/privacy_engine.py)
- [src/modules/reidentification.py](src/modules/reidentification.py)

---

**SynthLab v0.2** - Move Fast and Validate Things™ (Now with Privacy Guarantees!)
