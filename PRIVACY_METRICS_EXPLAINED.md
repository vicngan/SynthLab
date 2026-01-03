# Advanced Privacy Metrics - Complete Guide

## 🎯 Overview: Defense in Depth

SynthLab implements **four layers of privacy protection**:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Differential Privacy (DP)                         │
│  └─> Mathematical guarantee: (ε,δ)-DP                       │
│      "Output looks same with/without any individual"        │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: k-anonymity                                       │
│  └─> Structural guarantee: Hide in crowd of k people        │
│      "Can't distinguish you from k-1 others"                │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: l-diversity                                       │
│  └─> Attribute guarantee: l different sensitive values      │
│      "Even if in same group, outcome is uncertain"          │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: t-closeness                                       │
│  └─> Distribution guarantee: Similar to population          │
│      "Group distribution ≈ overall distribution"            │
└─────────────────────────────────────────────────────────────┘
```

## 📊 k-anonymity Explained

### Definition

A dataset satisfies **k-anonymity** if every record is indistinguishable from at least **k-1** other records based on quasi-identifiers.

**Quasi-identifiers**: Attributes that together could identify someone
- Examples: Age, Gender, ZIP code, Race, Occupation

### How It Works

#### Example: k=3 anonymity

**Original Data:**
```
ID  Age  Gender  ZipCode  Diagnosis  Salary
1   25   M       94101    Diabetes   $50K
2   25   M       94101    Asthma     $55K
3   25   M       94101    Healthy    $60K
4   30   F       94102    Diabetes   $65K
5   30   F       94102    Cancer     $70K
6   30   F       94102    Healthy    $75K
```

**Equivalence Classes (groups with same quasi-identifiers):**
```
Group A: (Age=25, Gender=M, ZIP=94101) → 3 people ✓
Group B: (Age=30, Gender=F, ZIP=94102) → 3 people ✓
```

✓ **Satisfies 3-anonymity** because all groups have ≥3 members!

**Violating k=3:**
```
ID  Age  Gender  ZipCode  Diagnosis
1   25   M       94101    Diabetes   ] Group A: 3 people ✓
2   25   M       94101    Asthma     ]
3   25   M       94101    Healthy    ]
4   45   F       94103    Cancer     ] Group B: 1 person ✗ UNIQUE!
```

❌ **Violates 3-anonymity** because Group B has only 1 member!

### Privacy Guarantee

**What an adversary knows:**
- "There's a 25-year-old male in ZIP 94101"

**What they can infer:**
- Without k-anonymity: Can identify the exact person
- With k=3 anonymity: Could be any of 3 people (33% confidence)
- With k=10 anonymity: Could be any of 10 people (10% confidence)

Higher k = Stronger privacy (but harder to achieve)

### Attacks k-anonymity Prevents

✅ **Linkage Attack**
```
Adversary has: "My neighbor is a 25-year-old male in ZIP 94101"
Without k-anonymity: Finds 1 matching record → knows neighbor's diagnosis
With k-anonymity: Finds k matching records → can't determine which one
```

### Limitations of k-anonymity

❌ **Homogeneity Attack** (solved by l-diversity)
```
Group: (Age=25, Gender=M, ZIP=94101)
- Person 1: Diabetes
- Person 2: Diabetes
- Person 3: Diabetes
```
k=3 satisfied ✓ BUT all have same diagnosis → adversary knows diagnosis!

❌ **Background Knowledge Attack**
```
Adversary knows: "My neighbor recently recovered from diabetes"
Group: (Age=25, Gender=M, ZIP=94101)
- Person 1: Diabetes
- Person 2: Asthma
- Person 3: Healthy (recent recovery from diabetes) ← IDENTIFIED!
```

---

## 🌈 l-diversity Explained

### Definition

A dataset satisfies **l-diversity** if each equivalence class contains at least **l "well-represented"** values for sensitive attributes.

**Sensitive attributes**: Data you want to protect
- Examples: Diagnosis, Salary, HIV status, Criminal record

### Types of l-diversity

#### 1. Distinct l-diversity (What we implement)

Each group must have **at least l different** sensitive values.

**Example: l=3 diversity**
```
Group: (Age=25, Gender=M, ZIP=94101)
Diagnoses: [Diabetes, Asthma, Healthy, Diabetes, Asthma]
Distinct values: {Diabetes, Asthma, Healthy} → 3 distinct ✓
```

#### 2. Entropy l-diversity

Entropy of sensitive values ≥ log(l)

**Formula:**
```
H(S) = -Σ p(s) × log(p(s)) ≥ log(l)
```

Where p(s) = probability of sensitive value s

**Example:**
```
Diagnoses: [Diabetes: 40%, Asthma: 30%, Healthy: 30%]
H = -(0.4×log(0.4) + 0.3×log(0.3) + 0.3×log(0.3))
  = 1.57 bits

For l=2: requires H ≥ log(2) = 1.0 ✓ Satisfies!
```

#### 3. Recursive (c,l)-diversity

Most frequent value appears ≤ c times more than others

### How It Protects Against Homogeneity Attack

**Without l-diversity:**
```
Group A: (Age=25, Gender=M, ZIP=94101)
- Diabetes
- Diabetes  } All same! ✗
- Diabetes

Adversary knows: You're in Group A
Adversary infers: You have diabetes (100% confidence)
```

**With l=3 diversity:**
```
Group A: (Age=25, Gender=M, ZIP=94101)
- Diabetes
- Asthma
- Healthy

Adversary knows: You're in Group A
Adversary infers: You might have diabetes (33% confidence)
```

### Calculating l-diversity

**Step 1: Group by quasi-identifiers**
```python
groups = df.groupby(['Age', 'Gender', 'ZipCode'])
```

**Step 2: Count distinct sensitive values per group**
```python
diversity = groups['Diagnosis'].nunique()
```

**Step 3: Check if all groups have ≥ l distinct values**
```python
satisfies = all(diversity >= l)
```

### Real-World Example

**Medical Dataset:**
```
Age  Gender  ZIP    Diagnosis    Group
25   M       94101  Diabetes     A
25   M       94101  Asthma       A
25   M       94101  Healthy      A
30   F       94102  Cancer       B
30   F       94102  Cancer       B  ← Only 1 distinct value!
30   F       94102  Cancer       B
```

**Check l=2 diversity:**
- Group A: {Diabetes, Asthma, Healthy} → 3 distinct ✓
- Group B: {Cancer} → 1 distinct ✗

**Result:** ❌ Does NOT satisfy 2-diversity

**Fix:** Add records or generalize attributes
```
Age  Gender  ZIP    Diagnosis
30   F       94102  Cancer
30   F       94102  Diabetes  ← Added diversity
30   F       94102  Cancer
```
Now Group B has 2 distinct values ✓

---

## 📏 t-closeness Explained

### Definition

A dataset satisfies **t-closeness** if the distribution of sensitive attributes in each equivalence class is **close** to the overall distribution, where "close" means distance ≤ t.

**Distance metric**: Earth Mover's Distance (Wasserstein distance)

### Why l-diversity is Not Enough

**Skewness Attack:**

**Overall distribution:**
- Healthy: 60%
- Diabetes: 30%
- Cancer: 10%

**Group A (Age=65+):**
- Healthy: 10%
- Diabetes: 10%
- Cancer: 80% ← Severely skewed!

Even with l=3 (distinct values), adversary can infer:
"If you're in Group A, you likely have cancer (80% vs 10% overall)"

**With t-closeness (t=0.2):**

**Group B (properly t-close):**
- Healthy: 55% (vs 60% overall, diff = 5%)
- Diabetes: 32% (vs 30% overall, diff = 2%)
- Cancer: 13% (vs 10% overall, diff = 3%)

Distance ≈ 0.10 < 0.2 ✓ Cannot infer sensitive info from group membership!

### Earth Mover's Distance (EMD)

**Intuition:** How much "work" to transform one distribution into another?

Think of distributions as piles of dirt:
```
Distribution A:  ████████░░  (80% here, 20% there)
Distribution B:  █████████░  (50% here, 50% there)

EMD = Amount of dirt moved × Distance
```

**Mathematical Formula:**

For discrete distributions:
```
EMD(P, Q) = Σ |P(x) - Q(x)| / 2
```

Where:
- P(x) = probability of value x in group distribution
- Q(x) = probability of value x in overall distribution

### Calculating t-closeness

**Example:**

**Overall distribution (entire dataset):**
```
Diagnosis     Probability
Healthy       0.60 (60%)
Diabetes      0.30 (30%)
Cancer        0.10 (10%)
```

**Group 1 distribution:**
```
Diagnosis     Probability   Difference
Healthy       0.55          |0.55 - 0.60| = 0.05
Diabetes      0.32          |0.32 - 0.30| = 0.02
Cancer        0.13          |0.13 - 0.10| = 0.03
```

**Distance calculation:**
```
EMD = (0.05 + 0.02 + 0.03) / 2 = 0.05
```

**Check t-closeness with t=0.2:**
```
0.05 ≤ 0.2  ✓ Satisfies t-closeness!
```

**Group 2 distribution (violates):**
```
Diagnosis     Probability   Difference
Healthy       0.10          |0.10 - 0.60| = 0.50
Diabetes      0.10          |0.10 - 0.30| = 0.20
Cancer        0.80          |0.80 - 0.10| = 0.70

EMD = (0.50 + 0.20 + 0.70) / 2 = 0.70
0.70 > 0.2  ✗ VIOLATES t-closeness!
```

### Attacks t-closeness Prevents

✅ **Skewness Attack**
```
Adversary knows: You're in elderly group (Age 65+)
Without t-closeness: 80% of elderly have cancer → high confidence
With t-closeness: 13% have cancer (similar to 10% overall) → low confidence
```

✅ **Similarity Attack**
```
Group has values: [50K, 51K, 52K, 53K] (all similar)
Overall distribution: [10K to 200K] (broad range)
Distance is HIGH → reveals you're likely in 50K range
t-closeness prevents this by requiring distribution similarity
```

### Choosing t Value

| t Value | Closeness Level | Use Case |
|---------|----------------|----------|
| 0.1 | Very strict | Highly sensitive attributes (HIV, salary) |
| 0.2 | **Recommended** | Medical diagnoses, demographics |
| 0.3 | Moderate | Less sensitive attributes |
| 0.5+ | Weak | May allow significant skewness |

---

## 🔄 How They Work Together

### The Complete Protection Stack

```
┌──────────────────────────────────────────────────────┐
│ DIFFERENTIAL PRIVACY (Layer 1)                       │
│ - Adds noise to data before synthesis                │
│ - Guarantees: (ε=1.0, δ=1e-5)-DP                    │
│ - Protects: Individual data points                   │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│ SYNTHETIC DATA GENERATION                            │
│ - Train CTGAN/TVAE/GaussianCopula on noisy data     │
│ - Generate 1000 synthetic records                    │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│ STRUCTURAL PRIVACY CHECKS (Layer 2-4)                │
│ - k-anonymity: Check group sizes ≥ k                │
│ - l-diversity: Check attribute diversity ≥ l        │
│ - t-closeness: Check distribution distance ≤ t      │
│ - If any fails → regenerate with different params   │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│ ✓ PRIVACY-SAFE SYNTHETIC DATA                       │
│ - Mathematically proven privacy (DP)                 │
│ - Structurally sound (k-anonymity)                   │
│ - Attribute protected (l-diversity)                  │
│ - Distribution preserved (t-closeness)               │
└──────────────────────────────────────────────────────┘
```

### Attack Scenarios & Defenses

| Attack Type | What Adversary Knows | Defense |
|-------------|---------------------|---------|
| **Linkage** | External database with your quasi-IDs | k-anonymity |
| **Homogeneity** | You're in a specific group | l-diversity |
| **Skewness** | Group demographics | t-closeness |
| **Reconstruction** | Multiple queries on dataset | Differential Privacy |
| **Membership Inference** | Dataset output statistics | Differential Privacy |

### Complementary Strengths

**DP provides:**
- ✅ Formal mathematical guarantee
- ✅ Works with any data type
- ❌ Doesn't catch structural issues
- ❌ High utility loss with small datasets

**k/l/t provide:**
- ✅ Interpretable privacy metrics
- ✅ Detect specific attack vectors
- ✅ Better utility on small datasets
- ❌ No formal mathematical proof

**Together:**
- ✅ **Best of both worlds!**
- ✅ Formal guarantees + practical validation
- ✅ Regulatory compliance (HIPAA + GDPR)

---

## 🎓 Practical Guidelines

### Recommended Parameter Settings

#### Medical Records (PHI)
```python
# Very strong privacy
dp_engine = DifferentialPrivacyEngine(epsilon=0.5, delta=1e-6)
analyzer = ReIdentificationAnalyzer(
    quasi_identifiers=['Age', 'Gender', 'ZipCode'],
    sensitive_attributes=['Diagnosis', 'Salary']
)
audit = analyzer.comprehensive_privacy_audit(k=5, l=3, t=0.1)
```

#### Research Datasets (De-identified)
```python
# Balanced privacy
dp_engine = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5)
audit = analyzer.comprehensive_privacy_audit(k=3, l=2, t=0.2)
```

#### Public Statistics (Aggregated)
```python
# Moderate privacy
dp_engine = DifferentialPrivacyEngine(epsilon=5.0, delta=1e-4)
audit = analyzer.comprehensive_privacy_audit(k=2, l=2, t=0.3)
```

### Troubleshooting Privacy Violations

#### k-anonymity Violations

**Problem:** Small groups with <k members

**Solutions:**
1. **Generalization**: Age 25 → Age 20-30
2. **Suppression**: Remove rare records
3. **Synthetic oversampling**: Generate more records for small groups

```python
# Example: Generalize Age
df['Age_Generalized'] = (df['Age'] // 10) * 10  # 25 → 20, 34 → 30
```

#### l-diversity Violations

**Problem:** Groups with homogeneous sensitive attributes

**Solutions:**
1. **Add diversity**: Ensure synthetic data varies within groups
2. **Merge groups**: Combine similar groups
3. **Relax l**: If l=3 fails, try l=2

```python
# Check which groups need more diversity
grouped = df.groupby(quasi_ids)['Diagnosis'].nunique()
print(grouped[grouped < l])  # Show violating groups
```

#### t-closeness Violations

**Problem:** Group distributions skewed vs overall

**Solutions:**
1. **Stratified sampling**: Generate proportional to overall distribution
2. **Reweighting**: Adjust synthesis probabilities
3. **Post-processing**: Resample to match target distribution

```python
# Resample to match overall distribution
target_dist = df['Diagnosis'].value_counts(normalize=True)
resampled = df.groupby('Diagnosis').sample(
    n=lambda x: int(len(x) * target_dist[x.name])
)
```

---

## 📊 Interpreting Privacy Audit Results

### Risk Level Matrix

| k-anon | l-div | t-close | Risk | Action |
|--------|-------|---------|------|--------|
| ✓ | ✓ | ✓ | **LOW** | ✅ Safe to share |
| ✓ | ✓ | ✗ | **MEDIUM** | ⚠️ Review distribution skew |
| ✓ | ✗ | ✓ | **MEDIUM** | ⚠️ Add attribute diversity |
| ✗ | ✓ | ✓ | **MEDIUM** | ⚠️ Increase group sizes |
| ✓ | ✗ | ✗ | **HIGH** | ⛔ Regenerate with constraints |
| ✗ | ✓ | ✗ | **HIGH** | ⛔ Generalize quasi-IDs |
| ✗ | ✗ | ✓ | **HIGH** | ⛔ Major structural issues |
| ✗ | ✗ | ✗ | **CRITICAL** | 🚨 Do not share |

### Example Audit Report

```
COMPREHENSIVE PRIVACY AUDIT
════════════════════════════════════════════════════

✓ k-anonymity (k=3): SATISFIED
  - All 150 groups have ≥3 members
  - Smallest group: 3 members
  - k-anonymity score: 100%

✗ l-diversity (l=2): VIOLATED
  - 12 groups with <2 distinct diagnoses
  - Violating groups: 8% of total
  - l-diversity score: 92%
  → Fix: Add diversity to 12 groups

✓ t-closeness (t=0.2): SATISFIED
  - Max distance: 0.18
  - Avg distance: 0.09
  - All groups within threshold

════════════════════════════════════════════════════
RISK ASSESSMENT
════════════════════════════════════════════════════
Metrics satisfied: 2/3
Risk level: MEDIUM
Recommendation: ⚠️ Review l-diversity violations
                Consider regenerating with l=2 constraint

Specific actions:
1. Regenerate data with diversity constraints
2. OR manually add diverse records to 12 groups
3. Re-run audit to verify
```

---

## 🔬 Advanced: Mathematical Proofs

### k-anonymity Theorem

**Theorem:** If a dataset satisfies k-anonymity, then for any quasi-identifier combination, an adversary cannot distinguish a target individual from k-1 others with probability > 1/k.

**Proof sketch:**
1. By definition, each QI combination has ≥k records
2. Adversary knows QI values → narrows to group of k records
3. Without additional info, each of k records equally likely
4. P(correct identification) = 1/k ≤ 1/k (equality when k exact)

### l-diversity Theorem

**Theorem:** If a dataset satisfies l-diversity, then for any quasi-identifier combination, an adversary cannot infer a sensitive value with confidence > 1/l.

**Proof sketch:**
1. By definition, each group has ≥l distinct sensitive values
2. Adversary knows QI → narrows to group
3. Group has ≥l values → entropy H ≥ log(l)
4. Maximum probability of any single value ≤ 1/l

### Composition Theorems

**Sequential Composition (DP):**
```
If M₁ satisfies ε₁-DP and M₂ satisfies ε₂-DP,
then (M₁, M₂) satisfies (ε₁ + ε₂)-DP
```

**Parallel Composition (DP):**
```
If M₁ operates on disjoint D₁ with ε₁-DP
and M₂ operates on disjoint D₂ with ε₂-DP,
then (M₁, M₂) satisfies max(ε₁, ε₂)-DP
```

This is why our budget tracking is critical!

---

## 📚 References & Further Reading

1. **k-anonymity:**
   - Sweeney, L. (2002). "k-anonymity: A model for protecting privacy"
   - IEEE Security & Privacy

2. **l-diversity:**
   - Machanavajjhala et al. (2007). "l-diversity: Privacy beyond k-anonymity"
   - ACM TKDD

3. **t-closeness:**
   - Li et al. (2007). "t-closeness: Privacy beyond k-anonymity and l-diversity"
   - IEEE ICDE

4. **Differential Privacy:**
   - Dwork, C. (2006). "Differential Privacy"
   - ICALP

5. **SynthLab Implementation:**
   - [privacy_engine.py](src/modules/privacy_engine.py)
   - [reidentification.py](src/modules/reidentification.py)
   - [DIFFERENTIAL_PRIVACY_EXPLAINED.md](DIFFERENTIAL_PRIVACY_EXPLAINED.md)
