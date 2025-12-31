import pandas as pd
import numpy as np
from typing import Dict

class QualityReport:
    #units for common medical statistics
    UNITS = {
        'Pregnancies': 'count',
        'Glucose': 'mg/dL',
        'BloodPressure': 'mm Hg',
        'SkinThickness': 'mm',
        'Insulin': 'uU/mL',
        'BMI': 'kg/m^2',
        'DiabetesPedigreeFunction': 'score',
        'Age': 'years',
        'Outcome': '0/1'
    }

    """Compare data quality between original and synthetic datasets"""
    def __init__(self, real_df: pd. DataFrame, synthetic_df: pd.DataFrame):
        self.real_df = real_df
        self.synthetic_df = synthetic_df    

    def compare_stats(self) -> Dict:
        """Compare basic statistics between real and synthetic data"""
        report = {}
        
        for col in self.real_df.select_dtypes(include=['number']).columns: 
            real_mean = self.real_df[col].mean()
            synth_mean = self.synthetic_df[col].mean()

            real_std = self.real_df[col].std()
            synth_std = self.synthetic_df[col].std()        

            #percent difference calculation
            mean_diff = abs(real_mean - synth_mean) / abs(real_mean) * 100 if real_mean != 0 else np.nan
            std_diff = abs(real_std - synth_std) / abs(real_std) * 100 if real_std != 0 else np.nan

            report[col] = {
                'unit': self.UNITS.get(col, ''),
                'real_mean': round(real_mean, 2),
                'synth_mean': round(synth_mean, 2),
                'mean_diff_%': mean_diff,
                'real_std': round(real_std, 2),
                'synth_std': round(synth_std, 2),
                'std_diff_%': round(std_diff, 2)
            }
        return report
            
    def plot_distributions(self):
        """Plot distributions of real vs synthetic data for numeric columns"""
        
        import plotly.graph_objects as go 

        figures = {}

        for col in self.real_df.select_dtypes(include=['number']).columns:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=self.real_df[col],
                name='Real Data',
                opacity=0.7,
                nbinsx=30,
                marker_color ='blue'
            ))
            fig.add_trace(go.Histogram(
                x=self.synthetic_df[col],
                name='Synthetic Data',
                opacity=0.7,
                nbinsx=30,
                marker_color='orange'
            ))

            unit = self.UNITS.get(col, '')
            fig.update_layout(
                title=f'Distribution of {col}',
                xaxis_title=col,
                yaxis_title='count',
                barmode='overlay'
            )

            figures[col] = fig

        return figures
    
    def compare_correlation(self):

        """
        Compare correlation matrices between real and synthetic data
        
        Returns:
            Tuple of (real_corr, synthetic_corr, diff) as DataFrames
        """

        numeric_real = self.real_df.select_dtypes(include=['number'])
        numeric_synth = self.synthetic_df.select_dtypes(include=['number'])

        real_corr = numeric_real.corr()
        synth_corr = numeric_synth.corr()
        diff = abs(real_corr - synth_corr)

        return real_corr, synth_corr, diff
    
    def plot_correlation_heatmaps(self):
        """Plot correlation heatmaps for real and synthetic data"""
        import plotly.express as px

        real_corr, synth_corr, diff = self.compare_correlation()

        fig_real = px.imshow(
            real_corr,
            text_auto = '.2f',
            color_continuous_scale='Blues',
            zmin=-1,
            zmax=1
        )

        fig_synth = px.imshow(
            synth_corr,
            text_auto = '.2f',
            color_continuous_scale='Oranges',
            zmin=-1,
            zmax=1
        )

        fig_diff = px.imshow(
            diff,
            text_auto = '.2f',
            color_continuous_scale='Reds',
            zmin=0,
            zmax=1
        )

        return fig_real, fig_synth, fig_diff

    def check_privacy(self):
        """
        Check if synthetic data maintains privacy
        
        Returns:
            Dict with privacy check results
        """
        #converting categorical columns to numeric for comparison
        real_rows= set(self.real_df.apply(tuple, axis=1))
        synth_rows = set(self.synthetic_df.apply(tuple, axis=1))

        #find exact matches
        leaked_rows = real_rows.intersection(synth_rows)
        leaked_percentage = len(leaked_rows) / len(real_rows) * 100

        return {
            'total_real_rows': len(self.real_df),
            'total_synthetic_rows': len(self.synthetic_df),
            'leaked_rows': len(leaked_rows),
            'leaked_percentage': leaked_percentage
        }
    
    def export_report(self, filename: str):
        """
        Export the quality report to a CSV file
        
        Args:
            filename: Name of the output CSV file
        Returns:
            Bytes of the exported CSV file
        """
        from fpdf import FPDF
        from io import BytesIO

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, txt="Quality Report", ln=True, align='C')
        pdf.ln(10)

        #stats table
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, txt="Basic Statistics", ln=True)
        pdf.set_font('Helvetica', '', 10)
        
        stats = self.compare_stats()
        for col, values in stats.items():
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 8, txt=f"{col} ({values['unit']})", ln=True)
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(0, 6, txt=f"  Real Mean: {values['real_mean']} | Synth Mean: {values['synth_mean']} | Diff: {values['mean_diff_%']:.2f}%", ln=True)
            pdf.cell(0, 6, txt=f"  Real Std: {values['real_std']} | Synth Std: {values['synth_std']} | Diff: {values['std_diff_%']:.2f}%", ln=True)
        
        #privacy check
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, txt="Privacy Check", ln=True)
        pdf.set_font('Helvetica', '', 10)

        privacy = self.check_privacy()
        pdf.cell(0, 10, txt=f"Total Real Rows: {privacy['total_real_rows']}", ln=True)
        pdf.cell(0, 10, txt=f"Total Synthetic Rows: {privacy['total_synthetic_rows']}", ln=True)
        pdf.cell(0, 10, txt=f"Leaked Rows: {privacy['leaked_rows']}", ln=True)

        if privacy['leaked_rows'] == 0:
            pdf.set_text_color(0, 128, 0)
            pdf.cell(0, 10, txt="Privacy Check Passed: No rows leaked", ln=True)
        else:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, txt=f"Privacy Check Failed: {privacy['leaked_percentage']}% of rows leaked", ln=True)
    
        #return the PDF as bytes
        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def ks_test(self) -> Dict:
        """
        Perform the Kolmogorov-Smirnov test to compare distributions of numeric columns
        
        Returns:
            Dict with KS test results for each numeric column
            Lower KS statistic and higher p-value indicate better fit between distributions.
            p-value < 0.05 suggests a significant difference between distributions.
            p-value > 0.05 suggests no significant difference between distributions.
        
        """
        
        from scipy import stats
        report = {}
        
        for col in self.real_df.select_dtypes(include=['number']).columns:
            ks_stat, p_value = stats.ks_2samp(
                self.real_df[col].dropna(), 
                self.synthetic_df[col]
            )

            report[col] = {
                'ks_statistic': round(ks_stat, 4),
                'p_value': round(p_value, 4),
                'similar': 'True' if p_value > 0.05 else 'False'
            }
        return report

    def distance_to_closest_record(self) -> pd.Series:
        """
        Calculate the distance to the closest record in the real dataset for each synthetic record.

        Measure of how similar each synthetic record is to the nearest real record.
        Higher distances indicate more uniqueness in synthetic data = better privacy.
        If any synthetic record has a distance of 0 or close , there is a privacy risk.
        
        Returns:
            Dict with distances for each synthetic record
        """
        from sklearn.neighbors import NearestNeighbors
        from sklearn.preprocessing import StandardScaler

        #use only numeric columns for distance calculation
        numeric_real = self.real_df.select_dtypes(include=['number']).columns.tolist() #list of numeric columns

        real_numeric = self.real_df[numeric_real].dropna() #ensure no NaNs
        synth_numeric = self.synthetic_df[numeric_real].dropna()

        #normalize data
        scaler = StandardScaler()
        real_scaled = scaler.fit_transform(real_numeric)
        synth_scaled = scaler.transform(synth_numeric)

        #find distances to closest real record
        nbrs = NearestNeighbors(n_neighbors=1, algorithm='auto').fit(real_scaled)
        nbrs.fit(real_scaled)
        distances, _ = nbrs.kneighbors(synth_scaled)

        distances = distances.flatten()

        #calculate statistics on distances
        min_distance = float(distances.min())
        mean_distance = float(distances.mean())
        max_distance = float(distances.max())
        median_distance = float(np.median(distances))

        #count how many synthetic records are very close to real records (threshold = 0.5 in normalized space)
        threshold = 0.5
        too_close = int((distances < threshold).sum())
        too_close_percentage = round(too_close / len(distances) * 100, 2)
        total_records = len(distances)

        #privacy risk if any records are too close
        privacy_risk = round(min(100, mean_distance * 20), 2)  #scaled to 0-100

        return {
            "min_distance": round(min_distance, 4),
            "mean_distance": round(mean_distance, 4),
            "max_distance": round(max_distance, 4),
            "median_distance": round(median_distance, 4),
            "privacy_risk_score": privacy_risk,
            "too_close_percentage": too_close_percentage,
            "close_records": too_close,
            "total_records": total_records,
            "threshold": threshold
        }
    def flip_test(self, protected_columns: str, model=None) -> Dict:
        """
        Perform Flip Test for fairness evaluation on protected attributes.
        
        Args:
            protected_columns: Comma-separated string of protected column names
            model: Pre-trained classification model with a predict method
        Returns:
            Dict with Flip Test results
        """

        if protected_columns not in self.synthetic_df.columns:
            raise ValueError(f"Protected column '{protected_columns}' not found in synthetic data.")
        
        unique_values = self.synthetic_df[protected_columns].unique()

        if len(unique_values) !=2:
            raise ValueError(f"Flip Test currently supports only binary protected attributes.'{protected_columns}' has {len(unique_values)} unique values.")
        
        val_a, val_b = unique_values[0], unique_values[1]
        
        #split synthetic data based on protected attribute
        group_a = self.synthetic_df[self.synthetic_df[protected_columns] == val_a]
        group_b = self.synthetic_df[self.synthetic_df[protected_columns] == val_b]

        results = {
            'protected_column': protected_columns,
            'group_a_value': val_a,
            'group_a_count': len(group_a),
            'group_b_value': val_b,
            'group_b_count': len(group_b),
            'column_stats': {}
        }

        #compare statistics for other numeric columns between groups
        for col in self.synthetic_df.select_dtypes(include=['number']).columns:
            if col == protected_columns:
                continue
            
            mean_a = group_a[col].mean()
            mean_b = group_b[col].mean()
            diff = abs(mean_a - mean_b)
            diff_percentage = (diff / abs(mean_a) * 100) if mean_a !=0 else 0
            std_a = group_a[col].std()
            std_b = group_b[col].std()

            results['column_stats'][col] = {
                'group_a_mean': round(mean_a, 2),
                'group_b_mean': round(mean_b, 2),
                'mean_diff': round(abs(mean_a - mean_b), 2),
                'group_a_std': round(std_a, 2),
                'group_b_std': round(std_b, 2),
                'std_diff': round(abs(std_a - std_b), 2),
                'potential_bias': 'True' if diff_percentage > 20 else 'False'
            }

        biased_columns = sum(1 for stats in results['column_stats'].values() if stats['potential_bias'])
        results['total_biased_columns'] = biased_columns
        results['fairness_score'] = round((1 - biased_columns / len(results['column_stats'])) * 100, 2) if results['column_stats'] else 100.0

        return results