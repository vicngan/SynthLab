"""
SynthLab Enhanced UI - Version 1.0
Comprehensive synthetic data generation platform with:
- User authentication
- Privacy controls (differential privacy, k-anonymity, etc.)
- Constraint management
- Model caching
- Literature search
- User management (admin)

Author: SynthLab Development Team
Created: 2026-01-12
"""

import streamlit as st
import pandas as pd
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add src directory to sys.path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport
from src.modules.literature import LiteratureSearch, LITERATURE_AVAILABLE
from src.modules.privacy_engine import DifferentialPrivacyEngine
from src.modules.reidentification import ReIdentificationAnalyzer
from src.modules.constraint_manager import ConstraintManager
from src.modules.model_cache import ModelCache

# API Configuration
API_BASE_URL = "http://localhost:8000"  # Change for production

# Page configuration
st.set_page_config(
    page_title="SynthLab - Synthetic Data Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def init_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'result' not in st.session_state:
        st.session_state.result = {}
    if 'literature_search' not in st.session_state:
        st.session_state.literature_search = None
    if 'privacy_settings' not in st.session_state:
        st.session_state.privacy_settings = {
            'epsilon': 1.0,
            'delta': 1e-5,
            'noise_mechanism': 'gaussian',
            'k_anonymity': 3,
            'l_diversity': 2,
            't_closeness': 0.2,
            'enable_dp': False,
            'enable_constraints': False
        }


def login(username: str, password: str) -> bool:
    """
    Authenticate user and store token.

    Returns:
        True if login successful, False otherwise
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data['access_token']
            st.session_state.user_info = data['user']
            return True
        else:
            return False
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server. Please ensure the API is running on http://localhost:8000")
        return False
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False


def logout():
    """Clear authentication state."""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user_info = None
    st.rerun()


def get_auth_headers() -> Dict[str, str]:
    """Get authorization headers for API requests."""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def check_token_expiry():
    """Check if token is expired and prompt re-login."""
    if st.session_state.authenticated and st.session_state.token:
        try:
            response = requests.get(
                f"{API_BASE_URL}/auth/me",
                headers=get_auth_headers(),
                timeout=5
            )
            if response.status_code == 401:
                st.warning("⚠️ Your session has expired. Please login again.")
                logout()
        except:
            pass


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_login_page():
    """Render login page."""
    st.markdown('<p class="main-header">🧬 SynthLab</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Enterprise Synthetic Data Platform</p>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🔐 Login")
        st.markdown("Please login to access SynthLab features.")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="changeme123")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if username and password:
                    with st.spinner("Authenticating..."):
                        if login(username, password):
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                else:
                    st.warning("Please enter both username and password")

        st.markdown("---")
        st.markdown("""
        **Default Credentials:**
        - Username: `admin`
        - Password: `changeme123`

        **⚠️ Change default password before production use!**
        """)

        with st.expander("ℹ️ About SynthLab"):
            st.markdown("""
            **SynthLab** is a comprehensive platform for generating privacy-safe synthetic data.

            **Features:**
            - 🔬 Multiple synthesis methods (CTGAN, TVAE, GaussianCopula)
            - 🔒 Differential privacy with (ε,δ)-framework
            - 📊 Advanced privacy metrics (k-anonymity, l-diversity, t-closeness)
            - ⚙️ Configurable constraints and templates
            - 📚 RAG-powered literature search
            - 💾 Model caching for faster generation
            - 👥 Multi-user support with role-based access

            **Security:**
            - JWT token authentication
            - API key support for programmatic access
            - Per-user rate limiting
            - Audit logging for compliance
            """)


def render_sidebar():
    """Render sidebar with settings and user info."""
    with st.sidebar:
        # User info
        st.markdown("### 👤 User Profile")
        user = st.session_state.user_info
        st.markdown(f"""
        **Username:** {user['username']}
        **Role:** {user['role'].title()}
        **Email:** {user['email']}
        """)

        if st.button("🚪 Logout", use_container_width=True):
            logout()

        st.markdown("---")

        # Synthesis settings
        st.markdown("### ⚙️ Synthesis Settings")

        method = st.selectbox(
            "Synthesis Method",
            options=["CTGAN", "GaussianCopula", "TVAE"],
            help="CTGAN: Best quality, slower | GaussianCopula: Fast, good for correlations | TVAE: Balanced",
            index=0,
            key="synthesis_method"
        )

        num_rows = st.number_input(
            "Number of Rows",
            min_value=10,
            max_value=100000,
            value=1000,
            step=100,
            key="num_rows"
        )

        st.markdown("---")

        # Privacy settings
        st.markdown("### 🔒 Privacy Controls")

        enable_dp = st.checkbox(
            "Enable Differential Privacy",
            value=st.session_state.privacy_settings['enable_dp'],
            help="Add calibrated noise to protect individual privacy",
            key="enable_dp"
        )
        st.session_state.privacy_settings['enable_dp'] = enable_dp

        if enable_dp:
            st.markdown("**DP Parameters:**")

            epsilon = st.slider(
                "Epsilon (ε)",
                min_value=0.1,
                max_value=10.0,
                value=st.session_state.privacy_settings['epsilon'],
                step=0.1,
                help="Privacy budget: Lower = more private, less accurate",
                key="epsilon"
            )
            st.session_state.privacy_settings['epsilon'] = epsilon

            delta = st.select_slider(
                "Delta (δ)",
                options=[1e-6, 1e-5, 1e-4, 1e-3],
                value=st.session_state.privacy_settings['delta'],
                help="Failure probability: Typically 1/n where n = dataset size",
                key="delta"
            )
            st.session_state.privacy_settings['delta'] = delta

            noise_mech = st.radio(
                "Noise Mechanism",
                options=['gaussian', 'laplace'],
                index=0 if st.session_state.privacy_settings['noise_mechanism'] == 'gaussian' else 1,
                help="Gaussian: (ε,δ)-DP | Laplace: ε-DP only",
                key="noise_mechanism"
            )
            st.session_state.privacy_settings['noise_mechanism'] = noise_mech

        st.markdown("---")

        # Privacy thresholds
        st.markdown("### 📊 Privacy Thresholds")

        k = st.number_input(
            "k-anonymity (k)",
            min_value=2,
            max_value=20,
            value=st.session_state.privacy_settings['k_anonymity'],
            help="Minimum group size for quasi-identifiers",
            key="k_anonymity"
        )
        st.session_state.privacy_settings['k_anonymity'] = k

        l = st.number_input(
            "l-diversity (l)",
            min_value=2,
            max_value=10,
            value=st.session_state.privacy_settings['l_diversity'],
            help="Minimum distinct sensitive values per group",
            key="l_diversity"
        )
        st.session_state.privacy_settings['l_diversity'] = l

        t = st.slider(
            "t-closeness (t)",
            min_value=0.1,
            max_value=0.5,
            value=st.session_state.privacy_settings['t_closeness'],
            step=0.05,
            help="Maximum distance between group and overall distribution",
            key="t_closeness"
        )
        st.session_state.privacy_settings['t_closeness'] = t

        st.markdown("---")

        # Constraint settings
        enable_constraints = st.checkbox(
            "Enable Constraints",
            value=st.session_state.privacy_settings['enable_constraints'],
            help="Apply domain-specific constraints to synthetic data",
            key="enable_constraints"
        )
        st.session_state.privacy_settings['enable_constraints'] = enable_constraints

        return method, num_rows


def render_privacy_dashboard(clean_df, synthetic_df, quasi_identifiers=None, sensitive_attrs=None):
    """
    Render comprehensive privacy analysis dashboard.

    Args:
        clean_df: Original cleaned data
        synthetic_df: Generated synthetic data
        quasi_identifiers: List of quasi-identifier columns
        sensitive_attrs: List of sensitive attribute columns
    """
    st.markdown("### 🔒 Advanced Privacy Analysis")

    tabs = st.tabs([
        "📊 Overview",
        "🔐 Differential Privacy",
        "👥 k-Anonymity",
        "🌈 l-Diversity",
        "📏 t-Closeness",
        "📍 DCR Analysis"
    ])

    # Tab 1: Overview
    with tabs[0]:
        st.markdown("#### Privacy Metrics Summary")

        col1, col2, col3, col4 = st.columns(4)

        # Basic privacy check
        quality_report = QualityReport(clean_df, synthetic_df)
        privacy_check = quality_report.check_privacy()
        dcr = quality_report.distance_to_closest_record()

        with col1:
            st.metric(
                "Privacy Score",
                f"{100 - privacy_check['leaked_percentage']:.1f}%",
                delta=f"{-privacy_check['leaked_rows']} leaked" if privacy_check['leaked_rows'] > 0 else "✓ No leaks"
            )

        with col2:
            st.metric(
                "Avg DCR",
                f"{dcr['mean_distance']:.4f}",
                delta="✓ Good" if dcr['mean_distance'] > 0.1 else "⚠ Low"
            )

        with col3:
            dp_enabled = st.session_state.privacy_settings['enable_dp']
            st.metric(
                "Differential Privacy",
                "✓ Enabled" if dp_enabled else "❌ Disabled",
                delta=f"ε={st.session_state.privacy_settings['epsilon']}" if dp_enabled else None
            )

        with col4:
            constraints_enabled = st.session_state.privacy_settings['enable_constraints']
            st.metric(
                "Constraints",
                "✓ Applied" if constraints_enabled else "❌ None",
                delta=None
            )

        st.markdown("---")

        # Privacy recommendations
        st.markdown("#### 💡 Recommendations")

        recommendations = []

        if privacy_check['leaked_rows'] > 0:
            recommendations.append({
                "severity": "high",
                "message": f"⚠️ **High Risk**: {privacy_check['leaked_rows']} exact matches found. Enable differential privacy or increase synthesis model complexity."
            })

        if dcr['mean_distance'] < 0.05:
            recommendations.append({
                "severity": "medium",
                "message": f"⚠️ **Medium Risk**: Average DCR is {dcr['mean_distance']:.4f} (too low). Consider adjusting synthesis parameters."
            })

        if not dp_enabled:
            recommendations.append({
                "severity": "low",
                "message": "ℹ️ **Suggestion**: Enable differential privacy for formal privacy guarantees."
            })

        if not constraints_enabled:
            recommendations.append({
                "severity": "low",
                "message": "ℹ️ **Suggestion**: Apply constraints to ensure biomedically valid synthetic data."
            })

        if not recommendations:
            st.success("✅ **Excellent!** All privacy checks passed. Your synthetic data appears to be privacy-safe.")
        else:
            for rec in recommendations:
                if rec['severity'] == 'high':
                    st.error(rec['message'])
                elif rec['severity'] == 'medium':
                    st.warning(rec['message'])
                else:
                    st.info(rec['message'])

    # Tab 2: Differential Privacy
    with tabs[1]:
        st.markdown("#### (ε,δ)-Differential Privacy Analysis")

        if st.session_state.privacy_settings['enable_dp']:
            epsilon = st.session_state.privacy_settings['epsilon']
            delta = st.session_state.privacy_settings['delta']

            st.success(f"✅ Differential privacy is **enabled** with ε={epsilon}, δ={delta}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Privacy Budget**")
                st.markdown(f"""
                - **Epsilon (ε)**: {epsilon}
                - **Delta (δ)**: {delta}
                - **Mechanism**: {st.session_state.privacy_settings['noise_mechanism'].title()}
                - **Privacy Level**: {'Strong (ε ≤ 1)' if epsilon <= 1 else 'Moderate (ε > 1)'}
                """)

            with col2:
                st.markdown("**What This Means**")
                if epsilon <= 0.5:
                    st.markdown("""
                    🔒 **Very Strong Privacy**
                    - Individual records are well-protected
                    - Low risk of re-identification
                    - May have lower data utility
                    """)
                elif epsilon <= 1.0:
                    st.markdown("""
                    🔐 **Strong Privacy**
                    - Good balance of privacy and utility
                    - Suitable for most use cases
                    - Industry standard for sensitive data
                    """)
                else:
                    st.markdown("""
                    ⚠️ **Moderate Privacy**
                    - Higher data utility
                    - Consider additional protections
                    - Not recommended for highly sensitive data
                    """)
        else:
            st.warning("⚠️ Differential privacy is **disabled**. Enable it in the sidebar for formal privacy guarantees.")

            st.markdown("""
            **Why Use Differential Privacy?**
            - **Mathematical guarantee**: Formal proof of privacy protection
            - **Resistance to attacks**: Protects against linkage and membership inference
            - **Composable**: Can safely combine multiple analyses
            - **Gold standard**: Required by many privacy regulations
            """)

    # Tab 3: k-Anonymity
    with tabs[2]:
        st.markdown("#### k-Anonymity Analysis")

        if quasi_identifiers and len(quasi_identifiers) > 0:
            k_threshold = st.session_state.privacy_settings['k_anonymity']

            analyzer = ReIdentificationAnalyzer(
                real_data=clean_df,
                synthetic_data=synthetic_df,
                quasi_identifiers=quasi_identifiers
            )

            is_k_anon, violation_groups = analyzer.check_k_anonymity(k=k_threshold)

            if is_k_anon:
                st.success(f"✅ Dataset satisfies {k_threshold}-anonymity")
                st.markdown(f"All quasi-identifier groups have at least {k_threshold} members.")
            else:
                st.error(f"❌ Dataset violates {k_threshold}-anonymity")
                st.markdown(f"Found {len(violation_groups)} groups with fewer than {k_threshold} members.")

                if len(violation_groups) > 0:
                    st.markdown("**Violating Groups:**")
                    violation_df = pd.DataFrame([
                        {
                            'Group': str(group),
                            'Size': size,
                            'Missing': k_threshold - size
                        }
                        for group, size in list(violation_groups.items())[:10]
                    ])
                    st.dataframe(violation_df)

                    if len(violation_groups) > 10:
                        st.info(f"Showing 10 of {len(violation_groups)} violating groups...")
        else:
            st.info("ℹ️ Select quasi-identifiers below to analyze k-anonymity.")

            # Let user select quasi-identifiers
            all_columns = synthetic_df.columns.tolist()
            selected_qi = st.multiselect(
                "Select Quasi-Identifier Columns",
                options=all_columns,
                help="Columns that could be used to re-identify individuals (e.g., Age, Gender, ZIP code)"
            )

            if selected_qi and st.button("Analyze k-Anonymity"):
                st.rerun()

    # Tab 4: l-Diversity
    with tabs[3]:
        st.markdown("#### l-Diversity Analysis")

        if quasi_identifiers and sensitive_attrs and len(quasi_identifiers) > 0 and len(sensitive_attrs) > 0:
            l_threshold = st.session_state.privacy_settings['l_diversity']

            analyzer = ReIdentificationAnalyzer(
                real_data=clean_df,
                synthetic_data=synthetic_df,
                quasi_identifiers=quasi_identifiers,
                sensitive_attributes=sensitive_attrs
            )

            is_l_diverse, violation_groups = analyzer.check_l_diversity(l=l_threshold)

            if is_l_diverse:
                st.success(f"✅ Dataset satisfies {l_threshold}-diversity")
                st.markdown(f"All groups have at least {l_threshold} distinct sensitive values.")
            else:
                st.error(f"❌ Dataset violates {l_threshold}-diversity")
                st.markdown(f"Found {len(violation_groups)} groups with insufficient diversity.")
        else:
            st.info("ℹ️ Select quasi-identifiers and sensitive attributes to analyze l-diversity.")

    # Tab 5: t-Closeness
    with tabs[4]:
        st.markdown("#### t-Closeness Analysis")

        if quasi_identifiers and sensitive_attrs and len(quasi_identifiers) > 0 and len(sensitive_attrs) > 0:
            t_threshold = st.session_state.privacy_settings['t_closeness']

            analyzer = ReIdentificationAnalyzer(
                real_data=clean_df,
                synthetic_data=synthetic_df,
                quasi_identifiers=quasi_identifiers,
                sensitive_attributes=sensitive_attrs
            )

            is_t_close, violation_groups = analyzer.check_t_closeness(t=t_threshold)

            if is_t_close:
                st.success(f"✅ Dataset satisfies {t_threshold}-closeness")
                st.markdown(f"All group distributions are within {t_threshold} of the overall distribution.")
            else:
                st.error(f"❌ Dataset violates {t_threshold}-closeness")
                st.markdown(f"Found {len(violation_groups)} groups with distributions too different from overall.")
        else:
            st.info("ℹ️ Select quasi-identifiers and sensitive attributes to analyze t-closeness.")

    # Tab 6: DCR Analysis
    with tabs[5]:
        st.markdown("#### Distance to Closest Record (DCR)")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Min DCR", f"{dcr['min_distance']:.4f}")
        with col2:
            st.metric("Max DCR", f"{dcr['max_distance']:.4f}")
        with col3:
            st.metric("Mean DCR", f"{dcr['mean_distance']:.4f}")
        with col4:
            st.metric("Too Close %", f"{dcr['too_close_percentage']}%")

        st.markdown("---")

        if dcr['too_close_percentage'] < 5:
            st.success(f"✅ **Strong Privacy**: Only {dcr['close_records']} of {dcr['total_synthetic']} records are suspiciously similar to real records.")
        else:
            st.warning(f"⚠️ **Privacy Risk**: {dcr['close_records']} of {dcr['total_synthetic']} records are too close to real records.")

        st.markdown("""
        **DCR Interpretation:**
        - **DCR ≥ 0.1**: Good separation, low re-identification risk
        - **DCR < 0.1**: Potentially too similar, review synthesis parameters
        - **DCR ≈ 0**: Possible exact or near-exact match, high risk
        """)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    init_session_state()
    check_token_expiry()

    # Show login page if not authenticated
    if not st.session_state.authenticated:
        render_login_page()
        return

    # Main application
    st.markdown('<p class="main-header">🧬 SynthLab v1.0</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate privacy-safe synthetic data with enterprise-grade security</p>', unsafe_allow_html=True)

    # Render sidebar
    method, num_rows = render_sidebar()

    # Main tabs
    tabs = st.tabs([
        "🔬 Synthetic Data",
        "📊 Advanced Privacy",
        "⚙️ Constraints",
        "💾 Model Cache",
        "📚 Literature Search",
        "👥 User Management" if st.session_state.user_info['role'] == 'admin' else None
    ])

    # Remove None from tabs if not admin
    tabs = [tab for tab in tabs if tab is not None]

    # Tab 1: Synthetic Data Generation
    with tabs[0]:
        st.markdown("### 📁 Upload Data")

        uploaded_files = st.file_uploader(
            "Upload CSV files",
            type=["csv"],
            accept_multiple_files=True,
            help="Upload one or more CSV files to generate synthetic data"
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.markdown("---")
                st.subheader(f"📄 {uploaded_file.name}")

                # Read CSV
                df = pd.read_csv(uploaded_file)
                st.markdown(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")

                # Data preview
                with st.expander("👁️ Data Preview"):
                    st.dataframe(df.head(10), use_container_width=True)

                # Generate button
                col1, col2 = st.columns([3, 1])

                with col1:
                    if st.button(f"🚀 Generate Synthetic Data", key=f"gen_{uploaded_file.name}", use_container_width=True):
                        with st.spinner(f"Generating {num_rows} synthetic rows..."):
                            # Clean data
                            loader = DataLoader(verbose=False)
                            clean_df, cols = loader.clean_data(df)

                            # Generate synthetic data
                            generator = SyntheticGenerator(method=method)
                            generator.train(clean_df)
                            synthetic_data = generator.generate(num_rows)

                            # Apply differential privacy if enabled
                            if st.session_state.privacy_settings['enable_dp']:
                                dp_engine = DifferentialPrivacyEngine(
                                    epsilon=st.session_state.privacy_settings['epsilon'],
                                    delta=st.session_state.privacy_settings['delta'],
                                    noise_mechanism=st.session_state.privacy_settings['noise_mechanism']
                                )

                                # Add noise to numeric columns
                                numeric_cols = synthetic_data.select_dtypes(include=['number']).columns.tolist()
                                if numeric_cols:
                                    synthetic_data_with_noise = dp_engine.add_noise_to_dataframe(
                                        synthetic_data[numeric_cols]
                                    )
                                    synthetic_data[numeric_cols] = synthetic_data_with_noise

                            # Apply constraints if enabled
                            if st.session_state.privacy_settings['enable_constraints']:
                                # Load clinical_labs template as example
                                constraint_file = Path("data/constraint_profiles/clinical_labs.json")
                                if constraint_file.exists():
                                    cm = ConstraintManager()
                                    cm.load_profile(str(constraint_file))
                                    synthetic_data = cm.apply_constraints(synthetic_data)

                            # Store results
                            st.session_state.result[uploaded_file.name] = {
                                'clean_data': clean_df,
                                'synthetic_data': synthetic_data,
                                'method': method
                            }

                        st.success(f"✅ Generated {len(synthetic_data)} synthetic rows!")
                        st.rerun()

                # Show results if available
                if uploaded_file.name in st.session_state.result:
                    result = st.session_state.result[uploaded_file.name]
                    clean_df = result['clean_data']
                    synthetic_data = result['synthetic_data']

                    # Synthetic data preview
                    with st.expander("🔬 Synthetic Data Preview"):
                        st.dataframe(synthetic_data.head(10), use_container_width=True)

                    # Download button
                    csv = synthetic_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Synthetic Data (CSV)",
                        data=csv,
                        file_name=f'synthetic_{uploaded_file.name}',
                        mime='text/csv',
                        key=f"download_{uploaded_file.name}",
                        use_container_width=True
                    )

                    # Quality metrics
                    st.markdown("### 📊 Quality Report")

                    quality_report = QualityReport(clean_df, synthetic_data)

                    # Statistical similarity
                    with st.expander("📈 Statistical Similarity"):
                        stats = quality_report.compare_stats()
                        st.dataframe(pd.DataFrame(stats).T, use_container_width=True)

                    # Basic privacy check
                    with st.expander("🔒 Privacy Check"):
                        privacy_check = quality_report.check_privacy()

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Real Rows", privacy_check["total_real_rows"])
                        col2.metric("Synthetic Rows", privacy_check["total_synthetic_rows"])
                        col3.metric("Leaked Rows", privacy_check['leaked_rows'])

                        if privacy_check["leaked_rows"] > 0:
                            st.warning(f"⚠️ Privacy Score: {100-privacy_check['leaked_percentage']:.1f}% - {privacy_check['leaked_rows']} exact matches found!")
                        else:
                            st.success(f"✅ Privacy Score: 100% - No exact matches found!")

                    # Distribution plots
                    with st.expander("📊 Distribution Comparison"):
                        figures = quality_report.plot_distributions()
                        for col_name, fig in list(figures.items())[:3]:  # Show first 3
                            st.plotly_chart(fig, use_container_width=True)

                        if len(figures) > 3:
                            st.info(f"Showing 3 of {len(figures)} distributions. See full report for all columns.")

    # Tab 2: Advanced Privacy Analysis
    with tabs[1]:
        st.markdown("### 🔒 Advanced Privacy Analysis")

        if not st.session_state.result:
            st.info("ℹ️ Generate synthetic data first to access privacy analysis.")
        else:
            # Select dataset to analyze
            dataset_name = st.selectbox(
                "Select Dataset",
                options=list(st.session_state.result.keys())
            )

            if dataset_name:
                result = st.session_state.result[dataset_name]
                clean_df = result['clean_data']
                synthetic_df = result['synthetic_data']

                # Select quasi-identifiers and sensitive attributes
                all_columns = synthetic_df.columns.tolist()

                col1, col2 = st.columns(2)

                with col1:
                    quasi_ids = st.multiselect(
                        "Quasi-Identifiers",
                        options=all_columns,
                        help="Columns that could be used together to re-identify individuals"
                    )

                with col2:
                    sensitive_attrs = st.multiselect(
                        "Sensitive Attributes",
                        options=all_columns,
                        help="Columns containing sensitive information to protect"
                    )

                if quasi_ids or sensitive_attrs:
                    render_privacy_dashboard(clean_df, synthetic_df, quasi_ids, sensitive_attrs)

    # Tab 3: Constraint Management
    with tabs[2]:
        st.markdown("### ⚙️ Constraint Templates")

        st.markdown("""
        Apply domain-specific constraints to ensure biomedically valid synthetic data.

        **Available Templates:**
        - **Clinical Labs**: Age, vital signs, lab values (glucose, cholesterol, etc.)
        - **Custom**: Create your own constraint profiles
        """)

        # List available templates
        template_dir = Path("data/constraint_profiles")
        if template_dir.exists():
            templates = list(template_dir.glob("*.json"))

            if templates:
                template_names = [t.stem for t in templates]
                selected_template = st.selectbox(
                    "Select Template",
                    options=template_names
                )

                if selected_template:
                    template_path = template_dir / f"{selected_template}.json"

                    with open(template_path, 'r') as f:
                        template_data = json.load(f)

                    st.markdown(f"**Template:** {template_data['name']}")
                    st.markdown(f"**Version:** {template_data['metadata']['version']}")
                    st.markdown(f"**Created:** {template_data['metadata']['created']}")

                    st.markdown("**Constraints:**")

                    constraints_df = pd.DataFrame([
                        {
                            'Column': c['column'],
                            'Type': c['constraint_type'],
                            'Parameters': str(c['params'])
                        }
                        for c in template_data['constraints']
                    ])

                    st.dataframe(constraints_df, use_container_width=True)

    # Tab 4: Model Cache
    with tabs[3]:
        st.markdown("### 💾 Model Cache")

        st.markdown("""
        View cached models to speed up repeated synthesis operations.

        **Benefits:**
        - 150x faster than re-training
        - Automatic content-based hashing
        - LRU eviction when cache full
        """)

        cache_dir = Path("cache/models")
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.meta.json"))

            if cache_files:
                st.markdown(f"**Cached Models:** {len(cache_files)}")

                cache_data = []
                for meta_file in cache_files:
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                        cache_data.append({
                            'Cache Key': meta['cache_key'][:20] + '...',
                            'Method': meta['method'],
                            'Data Shape': f"{meta['data_shape'][0]}×{meta['data_shape'][1]}",
                            'Size (MB)': f"{meta['file_size_mb']:.4f}",
                            'Training Time (s)': meta['training_time_sec'],
                            'Last Accessed': meta['last_accessed']
                        })

                cache_df = pd.DataFrame(cache_data)
                st.dataframe(cache_df, use_container_width=True)
            else:
                st.info("No models cached yet. Generate synthetic data to populate the cache.")
        else:
            st.info("Cache directory not found. It will be created when you generate synthetic data.")

    # Tab 5: Literature Search
    with tabs[4]:
        st.markdown("### 📚 Literature Intelligence")

        if not LITERATURE_AVAILABLE:
            st.error("Required libraries for Literature Search are not installed. Please install PyPDF2 and sentence-transformers.")
        else:
            uploaded_pdfs = st.file_uploader(
                "Upload Research Papers (PDF)",
                type=["pdf"],
                accept_multiple_files=True,
                key="pdf_uploader"
            )

            if uploaded_pdfs:
                if st.button("📖 Index Papers"):
                    with st.spinner("Processing PDFs and indexing..."):
                        if st.session_state.literature_search is None:
                            st.session_state.literature_search = LiteratureSearch()

                        for pdf_file in uploaded_pdfs:
                            pages = st.session_state.literature_search.add_pdf_bytes(
                                pdf_file.read(),
                                pdf_file.name
                            )
                            st.success(f"✅ Indexed {pages} pages from {pdf_file.name}")

                # Search interface
                if st.session_state.literature_search and st.session_state.literature_search.documents:
                    stats = st.session_state.literature_search.get_stats()
                    st.info(f"📚 Indexed: {stats['num_pages']} pages from {stats['num_documents']} documents")

                    query = st.text_input(
                        "Search Query",
                        placeholder="e.g., differential privacy in healthcare",
                        key="literature_query"
                    )

                    if query:
                        results = st.session_state.literature_search.search(query, top_k=5)

                        if results:
                            # AI summary
                            st.markdown("### 📝 AI Summary")
                            with st.spinner("Generating summary..."):
                                summary = st.session_state.literature_search.summarize_results(query, results)
                            st.markdown(summary)

                            # Source documents
                            st.markdown("### 📄 Source Documents")
                            for i, result in enumerate(results):
                                with st.expander(f"Result {i+1} - {result['filename']} (Score: {result['score']:.4f})"):
                                    st.markdown(result['text_snippet'])

    # Tab 6: User Management (Admin only)
    if len(tabs) > 5 and st.session_state.user_info['role'] == 'admin':
        with tabs[5]:
            st.markdown("### 👥 User Management")

            st.markdown("**Create New User**")

            with st.form("create_user_form"):
                col1, col2 = st.columns(2)

                with col1:
                    new_username = st.text_input("Username")
                    new_email = st.text_input("Email")

                with col2:
                    new_password = st.text_input("Password", type="password")
                    new_role = st.selectbox("Role", options=["researcher", "admin"])

                submit = st.form_submit_button("Create User", use_container_width=True)

                if submit:
                    if new_username and new_email and new_password:
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/auth/register",
                                headers=get_auth_headers(),
                                json={
                                    "username": new_username,
                                    "email": new_email,
                                    "password": new_password,
                                    "role": new_role
                                },
                                timeout=10
                            )

                            if response.status_code == 200:
                                user_data = response.json()
                                st.success(f"✅ User '{new_username}' created successfully!")
                                st.code(f"API Key: {user_data['api_key']}", language=None)
                            else:
                                st.error(f"❌ Failed to create user: {response.json().get('detail', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    else:
                        st.warning("Please fill all fields")


if __name__ == "__main__":
    main()
