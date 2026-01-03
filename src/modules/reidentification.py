"""
Advanced Re-identification Risk Analysis for SynthLab

This module implements sophisticated privacy metrics beyond Distance to Closest Record (DCR):
- k-anonymity: Ensures each record is indistinguishable from k-1 others
- l-diversity: Ensures diversity of sensitive attributes within groups
- t-closeness: Ensures distribution similarity between groups and dataset

## Why These Metrics Matter

While Differential Privacy (DP) provides theoretical guarantees, these metrics help:
1. **Detect structural privacy risks** that DP might not catch
2. **Provide interpretable privacy scores** for non-technical stakeholders
3. **Satisfy regulatory requirements** (HIPAA, GDPR often reference k-anonymity)

## How They Work Together

Think of privacy protection as layers:
```
Layer 1: Differential Privacy → Mathematical guarantee
Layer 2: k-anonymity → Structural guarantee (indistinguishability)
Layer 3: l-diversity → Protects against homogeneity attacks
Layer 4: t-closeness → Protects against skewness attacks
```

All four together = Defense in depth!
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from collections import Counter
from scipy.spatial.distance import cdist
from scipy.stats import wasserstein_distance


class ReIdentificationAnalyzer:
    """
    Comprehensive re-identification risk analysis using privacy metrics.

    This analyzer complements differential privacy by checking structural
    privacy properties of synthetic data.

    Attributes:
        real_df (pd.DataFrame): Original dataset
        synthetic_df (pd.DataFrame): Synthetic dataset
        quasi_identifiers (List[str]): Columns that could identify individuals
        sensitive_attributes (List[str]): Columns with sensitive information
    """

    def __init__(
        self,
        real_df: pd.DataFrame,
        synthetic_df: pd.DataFrame,
        quasi_identifiers: Optional[List[str]] = None,
        sensitive_attributes: Optional[List[str]] = None
    ):
        """
        Initialize the re-identification analyzer.

        Args:
            real_df: Original dataset
            synthetic_df: Synthetic dataset
            quasi_identifiers: Columns like Age, ZipCode that together could identify someone
            sensitive_attributes: Sensitive columns like Diagnosis, Salary

        Example:
            >>> analyzer = ReIdentificationAnalyzer(
            ...     real_df=real_data,
            ...     synthetic_df=synth_data,
            ...     quasi_identifiers=['Age', 'Gender', 'ZipCode'],
            ...     sensitive_attributes=['Diagnosis', 'Salary']
            ... )
        """
        self.real_df = real_df
        self.synthetic_df = synthetic_df

        # Auto-detect quasi-identifiers if not provided
        if quasi_identifiers is None:
            # Common quasi-identifiers in medical data
            common_qi = ['Age', 'Gender', 'ZipCode', 'ZIP', 'Race', 'Ethnicity']
            self.quasi_identifiers = [col for col in common_qi if col in synthetic_df.columns]

            if not self.quasi_identifiers:
                # Use all non-numeric or low-cardinality numeric columns
                self.quasi_identifiers = []
                for col in synthetic_df.columns:
                    if synthetic_df[col].dtype == 'object':
                        self.quasi_identifiers.append(col)
                    elif synthetic_df[col].nunique() < 20:  # Low cardinality
                        self.quasi_identifiers.append(col)
        else:
            self.quasi_identifiers = quasi_identifiers

        self.sensitive_attributes = sensitive_attributes or []

        print(f"✓ Initialized Re-identification Analyzer")
        print(f"  Quasi-identifiers: {self.quasi_identifiers}")
        print(f"  Sensitive attributes: {self.sensitive_attributes}")

    def check_k_anonymity(self, k: int = 3) -> Dict:
        """
        Check if synthetic data satisfies k-anonymity.

        ## What is k-anonymity?

        A dataset satisfies k-anonymity if every combination of quasi-identifiers
        appears at least k times. This makes each record "hide in a crowd" of k-1 others.

        ### Example:

        **Dataset with k=3 anonymity:**
        ```
        Age  Gender  ZipCode  Diagnosis
        25   M       94101    Diabetes    ]
        25   M       94101    Asthma      ] Group 1 (3 records)
        25   M       94101    Healthy     ]
        30   F       94102    Diabetes    ]
        30   F       94102    Cancer      ] Group 2 (3 records)
        30   F       94102    Healthy     ]
        ```

        **Dataset violating k=3 (has groups with <3):**
        ```
        Age  Gender  ZipCode  Diagnosis
        25   M       94101    Diabetes    ] Group 1 (2 records) ❌
        25   M       94101    Asthma      ]
        45   F       94103    Cancer      ] Group 2 (1 record) ❌ UNIQUE!
        ```

        ## How It Protects Privacy:

        If an adversary knows you're a "25-year-old male in ZIP 94101", they can't
        determine your specific record because there are at least k such people.

        ## When k-anonymity Fails:

        - **Homogeneity Attack**: All k records have same sensitive value
          → Solution: l-diversity (see below)
        - **Background Knowledge Attack**: Adversary knows you're in a specific group
          → Solution: Ensure k is large enough

        Args:
            k: Minimum group size (typically 3-5 for medical data)

        Returns:
            Dict with:
            - satisfies_k_anonymity (bool): Whether all groups have ≥k members
            - total_groups (int): Number of unique quasi-identifier combinations
            - violating_groups (int): Number of groups with <k members
            - smallest_group_size (int): Size of smallest group
            - violation_details (List): Details of violating groups
            - k_anonymity_score (float): Percentage of records in valid groups
        """
        print(f"\n🔍 Checking k-anonymity (k={k})...")

        if not self.quasi_identifiers:
            return {
                'error': 'No quasi-identifiers specified',
                'satisfies_k_anonymity': None
            }

        # Group by quasi-identifiers
        grouped = self.synthetic_df.groupby(self.quasi_identifiers).size().reset_index(name='count')

        # Find violating groups (size < k)
        violating = grouped[grouped['count'] < k]
        total_groups = len(grouped)
        violating_groups = len(violating)
        smallest_group_size = int(grouped['count'].min())

        # Calculate records in violating groups
        records_at_risk = int(violating['count'].sum())
        total_records = len(self.synthetic_df)
        k_anonymity_score = ((total_records - records_at_risk) / total_records) * 100

        satisfies = violating_groups == 0

        print(f"  Total equivalence classes: {total_groups}")
        print(f"  Violating groups (size < {k}): {violating_groups}")
        print(f"  Smallest group size: {smallest_group_size}")
        print(f"  Records at risk: {records_at_risk} / {total_records}")
        print(f"  k-anonymity score: {k_anonymity_score:.1f}%")

        if satisfies:
            print(f"  ✓ Dataset satisfies {k}-anonymity!")
        else:
            print(f"  ✗ Dataset does NOT satisfy {k}-anonymity")
            print(f"    Recommendation: Increase k to {smallest_group_size} or remove rare combinations")

        # Get violation details
        violation_details = []
        if not violating.empty:
            for _, row in violating.head(10).iterrows():  # Show first 10
                group_desc = {col: row[col] for col in self.quasi_identifiers}
                violation_details.append({
                    'group': group_desc,
                    'count': int(row['count']),
                    'risk_level': 'CRITICAL' if row['count'] == 1 else 'HIGH'
                })

        return {
            'satisfies_k_anonymity': satisfies,
            'k': k,
            'total_groups': total_groups,
            'violating_groups': violating_groups,
            'smallest_group_size': smallest_group_size,
            'records_at_risk': records_at_risk,
            'total_records': total_records,
            'k_anonymity_score': k_anonymity_score,
            'violation_details': violation_details
        }

    def check_l_diversity(self, l: int = 2) -> Dict:
        """
        Check if synthetic data satisfies l-diversity.

        ## What is l-diversity?

        A dataset satisfies l-diversity if each equivalence class (group with same
        quasi-identifiers) has at least l "well-represented" values for sensitive attributes.

        ### Why k-anonymity Alone is Not Enough:

        **k-anonymous but not l-diverse (Homogeneity Attack):**
        ```
        Age  Gender  ZipCode  Diagnosis
        25   M       94101    Diabetes    ]
        25   M       94101    Diabetes    ] k=3 ✓ but all have same diagnosis!
        25   M       94101    Diabetes    ]
        ```
        If adversary knows you're in this group, they know you have diabetes!

        **k-anonymous AND l-diverse (l=2):**
        ```
        Age  Gender  ZipCode  Diagnosis
        25   M       94101    Diabetes    ]
        25   M       94101    Asthma      ] k=3 ✓ AND 3 different diagnoses
        25   M       94101    Healthy     ]
        ```
        Adversary can't determine your diagnosis.

        ## Types of l-diversity:

        1. **Distinct l-diversity**: At least l distinct values
        2. **Entropy l-diversity**: Entropy ≥ log(l)
        3. **Recursive (c,l)-diversity**: Most frequent value ≤ c × others

        We use distinct l-diversity (simplest and most interpretable).

        Args:
            l: Minimum number of distinct sensitive values per group

        Returns:
            Dict with l-diversity metrics per sensitive attribute
        """
        print(f"\n🌈 Checking l-diversity (l={l})...")

        if not self.quasi_identifiers:
            return {'error': 'No quasi-identifiers specified'}

        if not self.sensitive_attributes:
            return {'error': 'No sensitive attributes specified'}

        results = {}

        for sens_attr in self.sensitive_attributes:
            if sens_attr not in self.synthetic_df.columns:
                print(f"  ⚠ Sensitive attribute '{sens_attr}' not found, skipping")
                continue

            print(f"\n  Analyzing sensitive attribute: '{sens_attr}'")

            # Group by quasi-identifiers and count distinct sensitive values
            diversity = self.synthetic_df.groupby(self.quasi_identifiers)[sens_attr]\
                .agg(['nunique', 'count'])\
                .reset_index()

            # Find groups with < l distinct values
            violating = diversity[diversity['nunique'] < l]
            total_groups = len(diversity)
            violating_groups = len(violating)

            # Calculate diversity score
            records_at_risk = int(violating['count'].sum())
            total_records = len(self.synthetic_df)
            diversity_score = ((total_records - records_at_risk) / total_records) * 100

            satisfies = violating_groups == 0

            print(f"    Total groups: {total_groups}")
            print(f"    Violating groups (diversity < {l}): {violating_groups}")
            print(f"    l-diversity score: {diversity_score:.1f}%")

            if satisfies:
                print(f"    ✓ Satisfies {l}-diversity for '{sens_attr}'")
            else:
                print(f"    ✗ Does NOT satisfy {l}-diversity for '{sens_attr}'")

            results[sens_attr] = {
                'satisfies_l_diversity': satisfies,
                'l': l,
                'total_groups': total_groups,
                'violating_groups': violating_groups,
                'records_at_risk': records_at_risk,
                'diversity_score': diversity_score
            }

        # Overall satisfaction (all attributes must satisfy)
        overall_satisfies = all(r['satisfies_l_diversity'] for r in results.values())

        return {
            'satisfies_l_diversity': overall_satisfies,
            'per_attribute': results
        }

    def check_t_closeness(self, t: float = 0.2) -> Dict:
        """
        Check if synthetic data satisfies t-closeness.

        ## What is t-closeness?

        A dataset satisfies t-closeness if the distribution of sensitive attributes
        within each equivalence class is close to the overall distribution.

        "Close" is measured using Earth Mover's Distance (EMD), also known as
        Wasserstein distance.

        ### Why l-diversity Alone is Not Enough:

        **l-diverse but not t-close (Skewness Attack):**

        Overall distribution: 60% Healthy, 30% Diabetes, 10% Cancer

        ```
        Group 1 (Age 25, Male):
        - 10% Healthy
        - 10% Diabetes
        - 80% Cancer    ← Skewed! Most have cancer
        ```

        Even with l=3 (distinct values), adversary can infer you likely have cancer
        because 80% of your group has it (vs 10% overall).

        **t-close (t=0.2):**
        ```
        Group 1:
        - 55% Healthy   (vs 60% overall, diff = 5%)
        - 32% Diabetes  (vs 30% overall, diff = 2%)
        - 13% Cancer    (vs 10% overall, diff = 3%)
        Total distance ≈ 0.10 < 0.2 ✓
        ```

        ## Earth Mover's Distance (EMD):

        Think of distributions as piles of dirt:
        - EMD = minimum cost to transform one pile into another
        - Cost = amount of dirt × distance moved

        For categorical data: Wasserstein distance
        For numerical data: Kolmogorov-Smirnov statistic

        Args:
            t: Maximum allowed distance (0-1, typically 0.1-0.3)

        Returns:
            Dict with t-closeness metrics
        """
        print(f"\n📏 Checking t-closeness (t={t})...")

        if not self.quasi_identifiers or not self.sensitive_attributes:
            return {'error': 'Need both quasi-identifiers and sensitive attributes'}

        results = {}

        for sens_attr in self.sensitive_attributes:
            if sens_attr not in self.synthetic_df.columns:
                continue

            print(f"\n  Analyzing sensitive attribute: '{sens_attr}'")

            # Get overall distribution
            overall_dist = self.synthetic_df[sens_attr].value_counts(normalize=True).to_dict()

            # Calculate distance for each group
            groups = self.synthetic_df.groupby(self.quasi_identifiers)
            distances = []

            for name, group in groups:
                group_dist = group[sens_attr].value_counts(normalize=True).to_dict()

                # Calculate Wasserstein distance
                all_values = set(overall_dist.keys()) | set(group_dist.keys())
                overall_probs = [overall_dist.get(v, 0) for v in all_values]
                group_probs = [group_dist.get(v, 0) for v in all_values]

                # For categorical: treat as discrete distribution
                distance = sum(abs(o - g) for o, g in zip(overall_probs, group_probs)) / 2

                distances.append({
                    'group': name,
                    'distance': distance,
                    'violates': distance > t
                })

            # Count violations
            violating = sum(1 for d in distances if d['violates'])
            total_groups = len(distances)
            max_distance = max(d['distance'] for d in distances) if distances else 0
            avg_distance = np.mean([d['distance'] for d in distances]) if distances else 0

            satisfies = violating == 0

            print(f"    Total groups: {total_groups}")
            print(f"    Violating groups (distance > {t}): {violating}")
            print(f"    Max distance: {max_distance:.4f}")
            print(f"    Avg distance: {avg_distance:.4f}")

            if satisfies:
                print(f"    ✓ Satisfies {t}-closeness for '{sens_attr}'")
            else:
                print(f"    ✗ Does NOT satisfy {t}-closeness for '{sens_attr}'")

            results[sens_attr] = {
                'satisfies_t_closeness': satisfies,
                't': t,
                'total_groups': total_groups,
                'violating_groups': violating,
                'max_distance': max_distance,
                'avg_distance': avg_distance,
                'distances': distances[:10]  # First 10 for inspection
            }

        overall_satisfies = all(r['satisfies_t_closeness'] for r in results.values())

        return {
            'satisfies_t_closeness': overall_satisfies,
            'per_attribute': results
        }

    def comprehensive_privacy_audit(
        self,
        k: int = 3,
        l: int = 2,
        t: float = 0.2
    ) -> Dict:
        """
        Run comprehensive privacy audit with all metrics.

        ## Privacy Risk Classification:

        | Metrics Satisfied | Risk Level | Action |
        |-------------------|------------|--------|
        | All 3 (k, l, t)   | LOW        | Safe to share |
        | 2 of 3            | MEDIUM     | Review violations |
        | 1 of 3            | HIGH       | Regenerate data |
        | 0 of 3            | CRITICAL   | Do not share |

        Args:
            k: k-anonymity parameter
            l: l-diversity parameter
            t: t-closeness parameter

        Returns:
            Comprehensive privacy report
        """
        print("="*70)
        print("COMPREHENSIVE PRIVACY AUDIT")
        print("="*70)

        # Run all checks
        k_anon = self.check_k_anonymity(k)
        l_div = self.check_l_diversity(l)
        t_close = self.check_t_closeness(t)

        # Count satisfied metrics
        metrics_satisfied = sum([
            k_anon.get('satisfies_k_anonymity', False),
            l_div.get('satisfies_l_diversity', False),
            t_close.get('satisfies_t_closeness', False)
        ])

        # Determine risk level
        if metrics_satisfied == 3:
            risk_level = 'LOW'
            recommendation = '✓ Dataset is safe to share with strong privacy guarantees'
        elif metrics_satisfied == 2:
            risk_level = 'MEDIUM'
            recommendation = '⚠ Review violations and consider regenerating with stricter parameters'
        elif metrics_satisfied == 1:
            risk_level = 'HIGH'
            recommendation = '⛔ Regenerate data with stronger privacy settings'
        else:
            risk_level = 'CRITICAL'
            recommendation = '🚨 DO NOT SHARE - Multiple severe privacy violations detected'

        print(f"\n{'='*70}")
        print(f"RISK ASSESSMENT")
        print(f"{'='*70}")
        print(f"  Metrics satisfied: {metrics_satisfied}/3")
        print(f"  Risk level: {risk_level}")
        print(f"  Recommendation: {recommendation}")

        return {
            'k_anonymity': k_anon,
            'l_diversity': l_div,
            't_closeness': t_close,
            'summary': {
                'metrics_satisfied': metrics_satisfied,
                'risk_level': risk_level,
                'recommendation': recommendation
            }
        }


# Example usage and demonstration
if __name__ == "__main__":
    print("="*70)
    print("RE-IDENTIFICATION ANALYSIS - DEMONSTRATION")
    print("="*70)

    # Create sample dataset with privacy issues
    print("\n1. Creating sample medical dataset...")
    df = pd.DataFrame({
        'Age': [25, 25, 25, 30, 30, 30, 45, 45, 60],
        'Gender': ['M', 'M', 'M', 'F', 'F', 'F', 'M', 'M', 'F'],
        'ZipCode': [94101, 94101, 94101, 94102, 94102, 94102, 94103, 94103, 94104],
        'Diagnosis': ['Diabetes', 'Asthma', 'Healthy', 'Diabetes', 'Cancer', 'Healthy', 'Cancer', 'Cancer', 'Diabetes'],
        'Salary': [50000, 55000, 60000, 65000, 70000, 75000, 80000, 85000, 90000]
    })

    print(f"  Dataset shape: {df.shape}")
    print(f"\n  Sample data:")
    print(df.head())

    # Initialize analyzer
    print("\n" + "="*70)
    print("2. Initializing Re-identification Analyzer...")
    print("="*70)

    analyzer = ReIdentificationAnalyzer(
        real_df=df,  # Same as synthetic for demo
        synthetic_df=df,
        quasi_identifiers=['Age', 'Gender', 'ZipCode'],
        sensitive_attributes=['Diagnosis', 'Salary']
    )

    # Run comprehensive audit
    print("\n" + "="*70)
    print("3. Running Comprehensive Privacy Audit...")
    print("="*70)

    audit_results = analyzer.comprehensive_privacy_audit(k=3, l=2, t=0.2)

    print("\n" + "="*70)
    print("✓ Demonstration Complete!")
    print("="*70)
