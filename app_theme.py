"""
SynthLab Beautiful UI - Version 2.0
Modern design with light/dark theme, purple accent, and pill-shaped buttons

Author: SynthLab Development Team
Created: 2026-01-19
"""

import streamlit as st
import pandas as pd
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add src directory to sys.path
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
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="SynthLab - Synthetic Data Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# THEME-AWARE CSS
# ============================================================================

def apply_custom_css(theme='light'):
    """Apply beautiful CSS with theme support"""

    # Define colors based on theme
    if theme == 'dark':
        bg_primary = "#1a1a2e"
        bg_secondary = "#16213e"
        bg_card = "#0f3460"
        text_primary = "#ffffff"
        text_secondary = "#b8c1ec"
        border_color = "#533483"
    else:  # light
        bg_primary = "#f8f9fa"
        bg_secondary = "#ffffff"
        bg_card = "#ffffff"
        text_primary = "#2d3436"
        text_secondary = "#636e72"
        border_color = "#9b59b6"

    st.markdown(f"""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

        /* Global Styles */
        * {{
            font-family: 'Poppins', sans-serif;
        }}

        /* Main container */
        .main {{
            background: {bg_primary};
            padding-top: 0;
        }}

        /* Top Navigation Bar */
        .top-nav {{
            background: {bg_secondary};
            padding: 1rem 2rem;
            border-bottom: 3px solid #9b59b6;
            box-shadow: 0 2px 10px rgba(155, 89, 182, 0.2);
            margin: -1rem -1rem 2rem -1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .synthlab-title {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #9b59b6 0%, #e74c3c 50%, #3498db 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
            letter-spacing: -1px;
            margin: 0;
        }}

        .synthlab-subtitle {{
            color: {text_secondary};
            font-size: 0.9rem;
            margin-top: -0.25rem;
        }}

        /* Search Bar */
        .search-container {{
            flex-grow: 1;
            max-width: 500px;
            margin: 0 2rem;
        }}

        .search-bar {{
            width: 100%;
            padding: 0.75rem 1.5rem;
            border: 2px solid #9b59b6;
            border-radius: 50px;
            background: {bg_card};
            color: {text_primary};
            font-size: 0.95rem;
            transition: all 0.3s;
        }}

        .search-bar:focus {{
            outline: none;
            border-color: #e74c3c;
            box-shadow: 0 0 0 3px rgba(155, 89, 182, 0.2);
        }}

        /* Pill-shaped buttons */
        .pill-button {{
            padding: 0.6rem 1.5rem;
            border-radius: 50px;
            border: 2px solid #9b59b6;
            background: transparent;
            color: #9b59b6;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin: 0 0.5rem;
            display: inline-block;
        }}

        .pill-button:hover {{
            background: #9b59b6;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(155, 89, 182, 0.3);
        }}

        .pill-button.active {{
            background: linear-gradient(135deg, #9b59b6 0%, #e74c3c 100%);
            color: white;
            border-color: transparent;
        }}

        /* Sidebar - Highlighted border */
        [data-testid="stSidebar"] {{
            background: {bg_secondary};
            border-right: 4px solid #9b59b6;
            box-shadow: 4px 0 15px rgba(155, 89, 182, 0.2);
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background: {bg_secondary};
        }}

        [data-testid="stSidebar"] .stMarkdown {{
            color: {text_primary};
        }}

        [data-testid="stSidebar"] label {{
            color: {text_primary} !important;
            font-weight: 500;
        }}

        /* Streamlit buttons -> Pill-shaped */
        .stButton > button {{
            background: linear-gradient(135deg, #9b59b6 0%, #e74c3c 100%);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(155, 89, 182, 0.3);
        }}

        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(155, 89, 182, 0.4);
        }}

        /* Cards */
        .card {{
            background: {bg_card};
            border: 2px solid #9b59b6;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 8px 20px rgba(155, 89, 182, 0.15);
            margin-bottom: 2rem;
            transition: all 0.3s;
        }}

        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 30px rgba(155, 89, 182, 0.25);
        }}

        /* Metric Cards */
        .metric-card {{
            background: linear-gradient(135deg, #9b59b6 0%, #e74c3c 100%);
            border-radius: 20px;
            padding: 1.5rem;
            color: white;
            text-align: center;
            box-shadow: 0 8px 20px rgba(155, 89, 182, 0.3);
            transition: all 0.3s;
        }}

        .metric-card:hover {{
            transform: scale(1.05);
            box-shadow: 0 12px 30px rgba(155, 89, 182, 0.4);
        }}

        .metric-value {{
            font-size: 2.5rem;
            font-weight: 800;
            margin: 0.5rem 0;
        }}

        .metric-label {{
            font-size: 0.85rem;
            font-weight: 600;
            opacity: 0.95;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}

        .metric-delta {{
            font-size: 0.9rem;
            margin-top: 0.5rem;
            opacity: 0.9;
        }}

        /* Info boxes */
        .info-box {{
            background: linear-gradient(135deg, rgba(155, 89, 182, 0.1) 0%, rgba(52, 152, 219, 0.1) 100%);
            border-left: 4px solid #3498db;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            color: {text_primary};
            margin: 1rem 0;
        }}

        .success-box {{
            background: linear-gradient(135deg, rgba(46, 213, 115, 0.1) 0%, rgba(72, 219, 251, 0.1) 100%);
            border-left: 4px solid #2ed573;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            color: {text_primary};
            margin: 1rem 0;
        }}

        .warning-box {{
            background: linear-gradient(135deg, rgba(255, 234, 167, 0.2) 0%, rgba(253, 203, 110, 0.2) 100%);
            border-left: 4px solid #ffa502;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            color: {text_primary};
            margin: 1rem 0;
        }}

        .error-box {{
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(238, 90, 111, 0.1) 100%);
            border-left: 4px solid #ff6b6b;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            color: {text_primary};
            margin: 1rem 0;
        }}

        /* Theme toggle */
        .theme-toggle {{
            position: fixed;
            top: 1rem;
            right: 2rem;
            z-index: 999;
            background: {bg_card};
            border: 2px solid #9b59b6;
            border-radius: 50px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .theme-toggle:hover {{
            background: #9b59b6;
            color: white;
        }}

        /* Tabs - Pill-shaped */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 12px;
            background: transparent;
            margin-bottom: 2rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            background: {bg_card};
            border: 2px solid #9b59b6;
            border-radius: 50px;
            padding: 12px 28px;
            color: {text_primary};
            font-weight: 600;
            transition: all 0.3s;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            background: rgba(155, 89, 182, 0.1);
            transform: translateY(-2px);
        }}

        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #9b59b6 0%, #e74c3c 100%);
            color: white;
            border-color: transparent;
        }}

        /* File uploader */
        [data-testid="stFileUploader"] {{
            background: {bg_card};
            border: 3px dashed #9b59b6;
            border-radius: 20px;
            padding: 2rem;
            transition: all 0.3s;
        }}

        [data-testid="stFileUploader"]:hover {{
            border-color: #e74c3c;
            background: rgba(155, 89, 182, 0.05);
        }}

        /* Dataframe */
        .dataframe {{
            border-radius: 15px;
            overflow: hidden;
            border: 2px solid #9b59b6;
        }}

        /* Progress bar */
        .stProgress > div > div {{
            background: linear-gradient(135deg, #9b59b6 0%, #e74c3c 100%);
        }}

        /* Expander */
        .streamlit-expanderHeader {{
            background: {bg_card};
            border-radius: 15px;
            font-weight: 600;
            color: {text_primary};
            border: 2px solid #9b59b6;
        }}

        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Text colors */
        h1, h2, h3, h4, h5, h6, p, span, div {{
            color: {text_primary};
        }}

        /* Inputs */
        input, textarea, select {{
            background: {bg_card} !important;
            color: {text_primary} !important;
            border: 2px solid #9b59b6 !important;
            border-radius: 12px !important;
        }}

        /* Sliders */
        .stSlider > div > div > div {{
            background: #9b59b6 !important;
        }}

    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE & AUTHENTICATION
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'authenticated': False,
        'token': None,
        'user_info': None,
        'result': {},
        'literature_search': None,
        'theme': 'light',  # default theme
        'search_query': '',
        'privacy_settings': {
            'epsilon': 1.0,
            'delta': 1e-5,
            'noise_mechanism': 'gaussian',
            'k_anonymity': 3,
            'l_diversity': 2,
            't_closeness': 0.2,
            'enable_dp': False,
            'enable_constraints': False
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login(username: str, password: str) -> bool:
    """Authenticate user"""
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
        return False
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server. Ensure it's running on http://localhost:8000")
        return False
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False


def logout():
    """Clear authentication"""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user_info = None
    st.rerun()


def get_auth_headers() -> Dict[str, str]:
    """Get authorization headers"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


# ============================================================================
# BEAUTIFUL COMPONENTS
# ============================================================================

def render_top_nav():
    """Render top navigation bar with search and menu"""

    # Search query state
    if 'search_input' not in st.session_state:
        st.session_state.search_input = ''

    st.markdown(f"""
    <div class="top-nav">
        <div>
            <div class="synthlab-title">🧬 SynthLab</div>
            <div class="synthlab-subtitle">Privacy-Safe Synthetic Data Platform</div>
        </div>
        <div class="search-container">
            <input type="text" class="search-bar" placeholder="🔍 Search datasets, features, docs..."
                   value="{st.session_state.search_query}" readonly>
        </div>
        <div>
            <button class="pill-button" onclick="window.location.href='#generate'">Generate</button>
            <button class="pill-button" onclick="window.location.href='#privacy'">Privacy</button>
            <button class="pill-button" onclick="window.location.href='#docs'">Docs</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle in top-right
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🌓 Theme", key="theme_toggle"):
            st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
            st.rerun()


def render_metric_card(label: str, value: str, delta: Optional[str] = None, gradient: str = "default"):
    """Render beautiful metric card"""

    if gradient == "success":
        bg = "linear-gradient(135deg, #2ed573 0%, #48dbfb 100%)"
    elif gradient == "warning":
        bg = "linear-gradient(135deg, #ffa502 0%, #ff6348 100%)"
    elif gradient == "purple":
        bg = "linear-gradient(135deg, #9b59b6 0%, #e74c3c 100%)"
    else:
        bg = "linear-gradient(135deg, #9b59b6 0%, #e74c3c 100%)"

    delta_html = f"<div class='metric-delta'>{delta}</div>" if delta else ""

    st.markdown(f"""
    <div class="metric-card" style="background: {bg};">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_info_box(text: str, type: str = "info"):
    """Render info box"""
    st.markdown(f'<div class="{type}-box">{text}</div>', unsafe_allow_html=True)


# ============================================================================
# LOGIN PAGE
# ============================================================================

def render_login_page():
    """Beautiful login page"""

    # Apply CSS
    apply_custom_css(st.session_state.theme)

    # Center content
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem;">
            <div class="synthlab-title" style="font-size: 4rem;">🧬 SynthLab</div>
            <div class="synthlab-subtitle" style="font-size: 1.2rem; margin-top: 1rem;">
                Privacy-Safe Synthetic Data Generation
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.markdown("### 👋 Welcome Back")
        st.markdown("Sign in to access the platform")
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")

            st.markdown("<br>", unsafe_allow_html=True)

            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                if username and password:
                    with st.spinner("🔐 Authenticating..."):
                        if login(username, password):
                            st.success("✅ Welcome to SynthLab!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials")
                else:
                    st.warning("Please enter both username and password")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        render_info_box("""
        <strong>Default Credentials:</strong><br>
        Username: <code>admin</code> | Password: <code>changeme123</code><br>
        <small>⚠️ Change before production use</small>
        """, "info")


# ============================================================================
# SIDEBAR
# ============================================================================

def render_sidebar():
    """Render sidebar with highlighted border"""

    with st.sidebar:
        user = st.session_state.user_info

        # User profile card
        st.markdown(f"""
        <div class="card">
            <div style="text-align: center;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">👤</div>
                <div style="font-size: 1.3rem; font-weight: 700;">{user['username']}</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.25rem;">{user['role'].title()}</div>
                <div style="font-size: 0.85rem; opacity: 0.7; margin-top: 0.5rem;">{user['email']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Sign Out", use_container_width=True):
            logout()

        st.markdown("---")

        # Synthesis Settings
        st.markdown("### ⚙️ Synthesis Settings")

        method = st.selectbox(
            "Method",
            options=["CTGAN", "GaussianCopula", "TVAE"],
            help="Choose synthesis algorithm"
        )

        num_rows = st.slider(
            "Synthetic Rows",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100
        )

        st.markdown("---")

        # Privacy Controls
        st.markdown("### 🔒 Privacy Controls")

        enable_dp = st.toggle(
            "Enable Differential Privacy",
            value=st.session_state.privacy_settings['enable_dp']
        )
        st.session_state.privacy_settings['enable_dp'] = enable_dp

        if enable_dp:
            epsilon = st.slider(
                "ε (Privacy Budget)",
                min_value=0.1,
                max_value=10.0,
                value=float(st.session_state.privacy_settings['epsilon']),
                step=0.1,
                help="Lower = More Private"
            )
            st.session_state.privacy_settings['epsilon'] = epsilon

            # Privacy indicator
            if epsilon <= 0.5:
                level, color = "🔒 Very Strong", "#2ed573"
            elif epsilon <= 1.0:
                level, color = "🔐 Strong", "#3498db"
            else:
                level, color = "⚠️ Moderate", "#ffa502"

            st.markdown(f"""
            <div style="background: {color}; color: white; padding: 0.75rem;
                        border-radius: 50px; text-align: center; margin-top: 1rem;
                        font-weight: 600; font-size: 0.9rem;">
                {level}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Privacy Thresholds
        with st.expander("📊 Privacy Metrics"):
            k = st.number_input("k-anonymity", 2, 20, st.session_state.privacy_settings['k_anonymity'])
            st.session_state.privacy_settings['k_anonymity'] = k

            l = st.number_input("l-diversity", 2, 10, st.session_state.privacy_settings['l_diversity'])
            st.session_state.privacy_settings['l_diversity'] = l

            t = st.slider("t-closeness", 0.1, 0.5, float(st.session_state.privacy_settings['t_closeness']), 0.05)
            st.session_state.privacy_settings['t_closeness'] = t

        enable_constraints = st.toggle(
            "Apply Constraints",
            value=st.session_state.privacy_settings['enable_constraints']
        )
        st.session_state.privacy_settings['enable_constraints'] = enable_constraints

        return method, num_rows


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application"""
    init_session_state()

    # Apply theme
    apply_custom_css(st.session_state.theme)

    # Show login if not authenticated
    if not st.session_state.authenticated:
        render_login_page()
        return

    # Render top nav
    render_top_nav()

    # Render sidebar
    method, num_rows = render_sidebar()

    # Main content
    tabs = st.tabs(["🎨 Generate", "🔒 Privacy", "💾 Cache", "👥 Users" if st.session_state.user_info['role'] == 'admin' else "📚 Docs"])

    # TAB 1: GENERATE
    with tabs[0]:
        st.markdown("### 📁 Upload Your Data")

        uploaded_file = st.file_uploader(
            "Drop CSV file here or click to browse",
            type=["csv"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            df = pd.read_csv(uploaded_file)

            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                render_metric_card("Rows", f"{df.shape[0]:,}")
            with col2:
                render_metric_card("Columns", f"{df.shape[1]}")
            with col3:
                render_metric_card("Size", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
            with col4:
                render_metric_card("Method", method)

            # Preview
            with st.expander("👁️ Data Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            # Generate button
            if st.button("🚀 Generate Synthetic Data", use_container_width=True, type="primary"):
                with st.spinner("✨ Creating synthetic data..."):
                    try:
                        loader = DataLoader(verbose=False)
                        clean_df, cols = loader.clean_data(df)

                        generator = SyntheticGenerator(method=method)
                        generator.train(clean_df)
                        synthetic_data = generator.generate(num_rows)

                        # Apply DP
                        if st.session_state.privacy_settings['enable_dp']:
                            dp_engine = DifferentialPrivacyEngine(
                                epsilon=st.session_state.privacy_settings['epsilon'],
                                delta=st.session_state.privacy_settings['delta'],
                                noise_mechanism=st.session_state.privacy_settings['noise_mechanism']
                            )
                            numeric_cols = synthetic_data.select_dtypes(include=['number']).columns.tolist()
                            if numeric_cols:
                                synthetic_data[numeric_cols] = dp_engine.add_noise_to_dataframe(synthetic_data[numeric_cols])

                        # Apply constraints
                        if st.session_state.privacy_settings['enable_constraints']:
                            constraint_file = Path("data/constraint_profiles/clinical_labs.json")
                            if constraint_file.exists():
                                cm = ConstraintManager()
                                cm.load_profile(str(constraint_file))
                                synthetic_data = cm.apply_constraints(synthetic_data)

                        st.session_state.result[uploaded_file.name] = {
                            'clean_data': clean_df,
                            'synthetic_data': synthetic_data,
                            'method': method
                        }

                        render_info_box(f"✅ <strong>Success!</strong> Generated {len(synthetic_data):,} synthetic rows", "success")
                        st.rerun()

                    except Exception as e:
                        render_info_box(f"❌ <strong>Error:</strong> {str(e)}", "error")

            # Results
            if uploaded_file.name in st.session_state.result:
                result = st.session_state.result[uploaded_file.name]
                synthetic_data = result['synthetic_data']
                clean_df = result['clean_data']

                st.markdown("---")
                st.markdown("### 📊 Results")

                quality_report = QualityReport(clean_df, synthetic_data)
                privacy_check = quality_report.check_privacy()
                dcr = quality_report.distance_to_closest_record()

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    render_metric_card(
                        "Privacy Score",
                        f"{100 - privacy_check['leaked_percentage']:.0f}%",
                        "✓ No leaks" if privacy_check['leaked_rows'] == 0 else f"⚠ {privacy_check['leaked_rows']} leaks",
                        gradient="success" if privacy_check['leaked_rows'] == 0 else "warning"
                    )

                with col2:
                    render_metric_card(
                        "Mean DCR",
                        f"{dcr['mean_distance']:.3f}",
                        "✓ Good" if dcr['mean_distance'] > 0.1 else "⚠ Low",
                        gradient="success" if dcr['mean_distance'] > 0.1 else "warning"
                    )

                with col3:
                    dp_enabled = st.session_state.privacy_settings['enable_dp']
                    render_metric_card(
                        "Diff Privacy",
                        "✓ ON" if dp_enabled else "✗ OFF",
                        f"ε={st.session_state.privacy_settings['epsilon']}" if dp_enabled else "Disabled",
                        gradient="success" if dp_enabled else "warning"
                    )

                with col4:
                    render_metric_card(
                        "Rows Created",
                        f"{len(synthetic_data):,}",
                        method
                    )

                with st.expander("🔬 Synthetic Data", expanded=False):
                    st.dataframe(synthetic_data.head(20), use_container_width=True)

                csv = synthetic_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Synthetic Data",
                    data=csv,
                    file_name=f'synthetic_{uploaded_file.name}',
                    mime='text/csv',
                    use_container_width=True
                )

    # TAB 2: PRIVACY
    with tabs[1]:
        st.markdown("### 🔒 Privacy Analysis")

        if not st.session_state.result:
            render_info_box("ℹ️ Generate synthetic data first to access privacy analysis", "info")
        else:
            dataset_name = st.selectbox("Select Dataset", list(st.session_state.result.keys()))

            if dataset_name:
                result = st.session_state.result[dataset_name]
                clean_df = result['clean_data']
                synthetic_df = result['synthetic_data']

                quality_report = QualityReport(clean_df, synthetic_df)
                privacy_check = quality_report.check_privacy()
                dcr = quality_report.distance_to_closest_record()

                col1, col2, col3 = st.columns(3)

                with col1:
                    render_metric_card(
                        "Privacy Score",
                        f"{100 - privacy_check['leaked_percentage']:.1f}%",
                        f"{privacy_check['leaked_rows']} exact matches",
                        gradient="success" if privacy_check['leaked_rows'] == 0 else "warning"
                    )

                with col2:
                    render_metric_card(
                        "Mean DCR",
                        f"{dcr['mean_distance']:.4f}",
                        f"Min: {dcr['min_distance']:.4f}",
                        gradient="success" if dcr['mean_distance'] > 0.1 else "warning"
                    )

                with col3:
                    render_metric_card(
                        "Too Close",
                        f"{dcr['too_close_percentage']:.1f}%",
                        f"{dcr['close_records']} records",
                        gradient="success" if dcr['too_close_percentage'] < 5 else "warning"
                    )

                st.markdown("#### 💡 Recommendations")

                if privacy_check['leaked_rows'] == 0 and dcr['mean_distance'] > 0.1:
                    render_info_box("✅ <strong>Excellent Privacy!</strong> No exact matches and good separation.", "success")
                elif privacy_check['leaked_rows'] > 0:
                    render_info_box(f"⚠️ <strong>Risk:</strong> {privacy_check['leaked_rows']} exact matches. Enable DP.", "error")
                else:
                    render_info_box("⚠️ <strong>Low DCR:</strong> Some records too similar. Adjust parameters.", "warning")

    # TAB 3: CACHE
    with tabs[2]:
        st.markdown("### 💾 Model Cache")

        cache_dir = Path("cache/models")
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.meta.json"))

            if cache_files:
                col1, col2 = st.columns(2)
                with col1:
                    render_metric_card("Cached Models", f"{len(cache_files)}")
                with col2:
                    total_size = sum(f.stat().st_size for f in cache_dir.glob("*.pkl")) / (1024*1024)
                    render_metric_card("Total Size", f"{total_size:.1f} MB")

                cache_data = []
                for meta_file in cache_files:
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                        cache_data.append({
                            'Method': meta['method'],
                            'Shape': f"{meta['data_shape'][0]}×{meta['data_shape'][1]}",
                            'Size (MB)': f"{meta['file_size_mb']:.2f}",
                            'Training (s)': f"{meta['training_time_sec']:.1f}",
                            'Last Used': meta['last_accessed'][:10]
                        })

                st.dataframe(pd.DataFrame(cache_data), use_container_width=True)
            else:
                render_info_box("ℹ️ No cached models yet.", "info")
        else:
            render_info_box("ℹ️ Cache will be created on first generation.", "info")

    # TAB 4: USERS/DOCS
    with tabs[3]:
        if st.session_state.user_info['role'] == 'admin':
            st.markdown("### 👥 User Management")

            with st.form("create_user"):
                col1, col2 = st.columns(2)

                with col1:
                    new_username = st.text_input("Username")
                    new_password = st.text_input("Password", type="password")

                with col2:
                    new_email = st.text_input("Email")
                    new_role = st.selectbox("Role", ["researcher", "admin"])

                submit = st.form_submit_button("Create User", use_container_width=True)

                if submit and new_username and new_email and new_password:
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/auth/register",
                            headers=get_auth_headers(),
                            json={"username": new_username, "email": new_email, "password": new_password, "role": new_role},
                            timeout=10
                        )

                        if response.status_code == 200:
                            user_data = response.json()
                            render_info_box(f"✅ <strong>User Created!</strong><br>Username: {new_username}<br>API Key: <code>{user_data['api_key']}</code>", "success")
                        else:
                            render_info_box(f"❌ Error: {response.json().get('detail')}", "error")
                    except Exception as e:
                        render_info_box(f"❌ Error: {str(e)}", "error")
        else:
            st.markdown("### 📚 Documentation")
            render_info_box("""
            <strong>Quick Start:</strong><br>
            1. Upload CSV in Generate tab<br>
            2. Configure privacy settings<br>
            3. Click Generate<br>
            4. Analyze privacy metrics
            """, "info")


if __name__ == "__main__":
    main()
