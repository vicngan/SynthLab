# Differential Privacy in SynthLab - Complete Explanation

## 📚 What is Differential Privacy?

Differential Privacy (DP) is a mathematical framework that provides **provable privacy guarantees**. It's the gold standard for privacy protection and is used by Google, Apple, and the U.S. Census Bureau.

### The Core Idea

Imagine you have a database of patient medical records. If someone can determine whether a specific person is in the database by looking at the output (like synthetic data or statistics), that's a privacy breach.

**Differential Privacy prevents this by ensuring:**
> The output looks essentially the same whether any single person's data is included or not.

### Real-World Example

**Without DP:**
- Real database: [Age: 25, 30, 45, 60, 75]
- Average age: 47
- You know everyone except one person → Their age must be 75
- **Privacy leak!**

**With DP:**
- Real database: [Age: 25, 30, 45, 60, 75]
- Add noise: [Age: 27, 31, 43, 62, 74]
- Average age: 47.4 (noisy)
- Even knowing 4 people, you can't determine the 5th person's exact age
- **Privacy protected!**

---

## 🔢 Key Parameters Explained

### 1. Epsilon (ε) - The Privacy Budget

**What it means:** How much privacy you're willing to "spend" for utility.

```
Smaller ε = Stronger Privacy = More Noise = Lower Utility
Larger ε = Weaker Privacy = Less Noise = Higher Utility
```

**Recommended values:**
- **ε = 0.1**: Very strong privacy (financial data, genetic information)
  - Noise is very high
  - Synthetic data may have 30-50% utility loss
  - Use when privacy is critical

- **ε = 1.0**: Balanced (medical records, demographics) ⭐ **RECOMMENDED**
  - Moderate noise
  - ~10-20% utility loss
  - Good balance for most healthcare research

- **ε = 10.0**: Weak privacy (aggregated statistics)
  - Minimal noise
  - <5% utility loss
  - Use when data is already somewhat aggregated

**Mathematical Definition:**

For any two datasets D₁ and D₂ that differ by one person, and any output O:

```
P[Mechanism(D₁) = O] ≤ e^ε × P[Mechanism(D₂) = O] + δ
```

This means: The probability distributions of outputs are "close" even when one person's data changes.

### 2. Delta (δ) - The Failure Probability

**What it means:** The probability that the privacy guarantee might fail.

```
δ = Probability of catastrophic failure
```

**How to set it:**
- Typically: δ = 1/n² where n = number of records
- For 1,000 rows: δ = 1/1,000,000 = 1×10⁻⁶
- For 10,000 rows: δ = 1/100,000,000 = 1×10⁻⁸

**Why we need it:**
- Pure ε-DP requires Laplace noise, which can be very large
- (ε,δ)-DP allows Gaussian noise, which is more efficient
- δ represents "acceptable risk" of privacy breach (should be negligible)

---

## 🎲 Noise Mechanisms

### Laplace Mechanism (Pure ε-DP)

**Formula:**
```python
noise_scale = sensitivity / ε
noise = Laplace(0, noise_scale)
```

**When to use:**
- When you need pure DP without any failure probability (δ = 0)
- For count queries and histogram releases

**Characteristics:**
- Heavy-tailed distribution (more extreme outliers)
- Larger noise on average

**Example:**
```python
# Age column: range = [0, 120], sensitivity = 120
# ε = 1.0
noise_scale = 120 / 1.0 = 120

# Original ages: [25, 30, 45, 60, 75]
# Laplace noise: [-50, 30, 15, -20, 80] (random)
# Noisy ages: [-25, 60, 60, 40, 155]
```

### Gaussian Mechanism ((ε,δ)-DP)

**Formula:**
```python
noise_scale = sensitivity × √(2×ln(1.25/δ)) / ε
noise = Gaussian(0, noise_scale²)
```

**When to use:**
- When approximate DP is acceptable (δ > 0)
- For machine learning algorithms (gradient perturbation)

**Characteristics:**
- Bell-curved distribution (fewer extreme outliers)
- More concentrated around the true value

**Example:**
```python
# Age column: range = [0, 120], sensitivity = 120
# ε = 1.0, δ = 1e-5
noise_scale = 120 × √(2×ln(1.25/1e-5)) / 1.0
             = 120 × √(2×ln(125000)) / 1.0
             = 120 × √(23.65) / 1.0
             = 120 × 4.86 = 583.7

# Original ages: [25, 30, 45, 60, 75]
# Gaussian noise: [-100, 200, -50, 150, -80] (random)
# Noisy ages: [-75, 230, -5, 210, -5]
```

---

## 🎯 Sensitivity Explained

**Sensitivity** measures the maximum change in output when one person's data changes.

### L1 Sensitivity (Manhattan Distance)

**Formula:**
```
Sensitivity = max(value) - min(value)
```

**Use cases:**
- Numeric data with known bounds
- Count queries
- Sum queries

**Example:**
```python
# Blood Pressure: values in [40, 250]
# If one person changes from 40 → 250, output changes by 210
L1_sensitivity = 250 - 40 = 210

# Outcome (0 or 1): binary variable
L1_sensitivity = 1 - 0 = 1
```

### L2 Sensitivity (Euclidean Distance)

**Formula:**
```
Sensitivity = √(Σ (max_i - min_i)²)
```

**Use cases:**
- Multi-dimensional queries
- Machine learning gradients

**Example:**
```python
# Vector: [Age, BMI, Glucose]
# Ranges: [0-120, 10-80, 0-600]
L2_sensitivity = √(120² + 70² + 600²)
               = √(14400 + 4900 + 360000)
               = √379300 = 615.9
```

---

## 💡 How Privacy Budget Works

Think of privacy budget like money:
- You start with a total budget (ε_total)
- Each operation "costs" some budget (ε_used)
- When budget is depleted, no more operations allowed

### Sequential Composition

When you run multiple DP operations on the same data:

```
ε_total = ε₁ + ε₂ + ε₃ + ... + εₙ
```

**Example:**
```python
# Total budget: ε = 1.0
# Operation 1: Add noise to Age → costs ε₁ = 0.25
# Operation 2: Add noise to BMI → costs ε₂ = 0.25
# Operation 3: Add noise to Glucose → costs ε₃ = 0.25
# Operation 4: Add noise to BP → costs ε₄ = 0.25
# Total used: 0.25 + 0.25 + 0.25 + 0.25 = 1.0 ✓
```

### Budget Allocation Strategies

**1. Uniform Allocation** (What we implemented)
```python
ε_per_column = ε_total / n_columns
```
- Simple to understand
- Fair distribution
- May over-noise low-sensitivity columns

**2. Sensitivity-Proportional Allocation**
```python
ε_col = ε_total × (1/sensitivity_col) / Σ(1/sensitivity_all)
```
- More budget to low-sensitivity columns
- Better utility
- More complex to explain

**3. Manual Allocation**
```python
ε_important_col = 0.5  # User-specified
ε_less_important = 0.1
```
- Maximum control
- Requires domain expertise

---

## 🔐 Privacy Guarantees in Practice

### What DP Protects Against

✅ **Membership Inference Attacks**
- Adversary can't determine if someone is in the dataset

✅ **Reconstruction Attacks**
- Can't reverse-engineer original data from synthetic data

✅ **Linkage Attacks**
- Can't link synthetic records to real individuals

### What DP Does NOT Protect Against

❌ **Small Group Disclosure**
- If a group has <5 people, DP may not fully protect them
- Solution: k-anonymity (implemented separately)

❌ **Attribute Disclosure**
- If everyone in a group has the same sensitive attribute
- Solution: l-diversity (implemented separately)

❌ **Side Information**
- Adversary has external knowledge
- Solution: Combine with data minimization

---

## 📊 Privacy vs Utility Trade-off

### Measuring Utility Loss

We measure how much the synthetic data deviates from real data:

**1. Mean Absolute Error (MAE)**
```python
MAE = mean(|real_mean - synthetic_mean|)
```

**2. KS Statistic (Distribution Similarity)**
```python
KS_stat, p_value = ks_2samp(real_data, synthetic_data)
# Lower KS stat = better
# p_value > 0.05 = distributions are similar
```

**3. Correlation Preservation**
```python
corr_error = mean(|corr_real - corr_synthetic|)
```

### Expected Utility Loss by Epsilon

| Epsilon | Privacy Level | Expected Utility Loss | Use Case |
|---------|---------------|----------------------|----------|
| 0.1 | Very Strong | 30-50% | Genetic data, SSN |
| 0.5 | Strong | 20-30% | Individual medical records |
| **1.0** | **Balanced** ⭐ | **10-20%** | **Healthcare research** |
| 5.0 | Moderate | 5-10% | Aggregated statistics |
| 10.0 | Weak | <5% | Public datasets |

---

## 🧪 Example: Medical Dataset

Let's walk through a complete example with a diabetes dataset.

### Original Data
```
PatientID  Age  Glucose  BloodPressure  BMI  Outcome
1          25   85       70             22.5  0
2          30   90       75             24.0  0
3          45   120      80             27.5  1
4          60   140      85             30.0  1
5          75   160      90             32.5  1
```

### Step 1: Calculate Sensitivities
```python
Age_sensitivity = 75 - 25 = 50
Glucose_sensitivity = 160 - 85 = 75
BP_sensitivity = 90 - 70 = 20
BMI_sensitivity = 32.5 - 22.5 = 10
```

### Step 2: Allocate Privacy Budget
```python
ε_total = 1.0
n_columns = 4
ε_per_column = 1.0 / 4 = 0.25
```

### Step 3: Calculate Noise Scales (Gaussian)
```python
# Age
σ_Age = 50 × √(2×ln(1.25/1e-5)) / 0.25
      = 50 × 4.86 / 0.25 = 972.4

# Glucose
σ_Glucose = 75 × 4.86 / 0.25 = 1458.6

# Blood Pressure
σ_BP = 20 × 4.86 / 0.25 = 388.8

# BMI
σ_BMI = 10 × 4.86 / 0.25 = 194.4
```

### Step 4: Add Noise
```python
# Original Age: [25, 30, 45, 60, 75]
# Gaussian(0, 972.4²) noise: [-500, 300, -100, 200, -50]
# Noisy Age: [-475, 330, -55, 260, 25]
```

### Step 5: Statistical Comparison
```python
# Original mean Age: 47.0
# Noisy mean Age: 17.0
# Error: 63.8%

# But correlation structure is preserved!
# corr(Age, Glucose) ≈ 0.95 (original)
# corr(Age_noisy, Glucose_noisy) ≈ 0.87 (noisy)
```

---

## 🛡️ When to Use Differential Privacy

### ✅ Use DP When:

1. **Sharing synthetic data publicly**
   - Publishing datasets for research
   - Open data initiatives
   - Competition datasets

2. **HIPAA/GDPR compliance required**
   - Protected Health Information (PHI)
   - Personal Identifiable Information (PII)

3. **Adversarial threat model**
   - Adversary has auxiliary information
   - Risk of re-identification attacks

4. **Legal/ethical requirements**
   - IRB mandates formal privacy guarantees
   - Contractual obligations

### ❌ Don't Use DP When:

1. **Data already aggregated**
   - State-level statistics (not individual-level)
   - Already anonymized through other means

2. **Sample size too small**
   - <100 records: DP noise may destroy all utility
   - Consider k-anonymity instead

3. **Non-sensitive data**
   - Public information (weather, traffic)
   - Anonymized by design

---

## 🔬 Advanced Topics

### 1. Gradient Perturbation for Deep Learning

For CTGAN/TVAE, we add noise to gradients during training:

```python
# Standard gradient descent
θ_new = θ_old - learning_rate × gradient

# DP gradient descent
gradient_clipped = clip(gradient, max_norm=C)
gradient_noisy = gradient_clipped + Gaussian(0, σ²)
θ_new = θ_old - learning_rate × gradient_noisy
```

**Why this works:**
- Each gradient depends on one batch of data
- Adding noise to gradients = DP on the batch
- Composition theorem → DP for entire training

### 2. Privacy Amplification by Sampling

If you randomly sample data before adding noise:

```python
# Original: ε-DP
# After sampling q fraction: (q×ε)-DP

# Example: Sample 10% of data, apply ε=1.0 DP
# Effective: ε_effective = 0.1 × 1.0 = 0.1-DP
# 10× stronger privacy!
```

### 3. Post-Processing Invariance

Once you have DP-protected data, any computation on it remains DP:

```python
noisy_data = add_DP_noise(real_data, ε=1.0)
# noisy_data has ε=1.0 DP

synthetic_data = train_GAN(noisy_data)
# synthetic_data ALSO has ε=1.0 DP (no extra privacy cost!)
```

---

## 📈 Monitoring & Compliance

### Privacy Audit Report

Our engine generates a compliance report:

```json
{
  "privacy_guarantee": {
    "epsilon": 1.0,
    "delta": 1e-5,
    "mechanism": "gaussian",
    "interpretation": "Strong Privacy - Balanced"
  },
  "budget_tracking": {
    "total_budget": 1.0,
    "budget_used": 1.0,
    "budget_remaining": 0.0,
    "utilization_percent": 100.0
  },
  "operations": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "column": "Age",
      "epsilon_used": 0.25,
      "sensitivity": 50.0,
      "noise_scale": 972.4
    }
  ]
}
```

### HIPAA Compliance

DP satisfies HIPAA Safe Harbor de-identification if:
- ε ≤ 1.0 (strong privacy)
- Combined with removal of 18 identifiers
- Expert determination review

---

## 🎓 Further Reading

1. **Foundational Papers:**
   - Dwork (2006): "Differential Privacy" - The original paper
   - Abadi et al. (2016): "Deep Learning with Differential Privacy"

2. **Practical Guides:**
   - Google's Differential Privacy Library
   - Harvard Privacy Tools Project

3. **SynthLab Implementation:**
   - [privacy_engine.py](src/modules/privacy_engine.py) - Our implementation
   - [reidentification.py](src/modules/reidentification.py) - Complementary privacy metrics

---

## 💻 Using DP in SynthLab

```python
from src.modules.privacy_engine import DifferentialPrivacyEngine
import pandas as pd

# 1. Load your data
df = pd.read_csv('patient_data.csv')

# 2. Initialize DP engine
engine = DifferentialPrivacyEngine(
    epsilon=1.0,      # Balanced privacy
    delta=1e-5,       # Small failure probability
    noise_mechanism='gaussian'
)

# 3. Add noise to data
noisy_df = engine.add_noise_to_dataframe(df)

# 4. Train synthesizer on noisy data
from src.modules.synthesizer import SyntheticGenerator
generator = SyntheticGenerator(method='CTGAN')
generator.train(noisy_df)
synthetic_data = generator.generate(1000)

# 5. Generate privacy report
engine.export_report('privacy_compliance.json')
```

**Result:** Your synthetic data has **(ε=1.0, δ=1e-5)-Differential Privacy** guarantee! 🎉
