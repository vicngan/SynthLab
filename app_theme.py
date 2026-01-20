"""
SynthLab Clean Minimal UI - Version 3.0
Clean, minimal design inspired by modern web aesthetics

Author: SynthLab Development Team
Created: 2026-01-19
Updated: 2026-01-19
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

# Lazy imports to avoid SDV compatibility issues at startup
# Modules will be imported when needed
LITERATURE_AVAILABLE = False
try:
    from src.modules.literature import LITERATURE_AVAILABLE
except ImportError:
    pass

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
# CLEAN MINIMAL CSS
# ============================================================================

def apply_custom_css(theme='light'):
    """Apply Clinical Dark Mode CSS - precision, trust, high-tech capability"""

    # Clinical Dark Mode - Data-forward design
    if theme == 'dark':
        # Deep Gunmetal / Slate Grey palette
        bg_primary = "#0F172A"      # Deep gunmetal
        bg_secondary = "#1E293B"     # Slightly lighter slate
        bg_card = "#334155"          # Card background
        text_primary = "#F8FAFC"     # Almost white
        text_secondary = "#94A3B8"   # Slate gray
        border_color = "#475569"     # Subtle borders
        accent_color = "#14B8A6"     # Medical Teal
        accent_secondary = "#3B82F6" # Bioscience Blue
        success_color = "#10B981"    # Green
        warning_color = "#F59E0B"    # Amber
        error_color = "#EF4444"      # Red
    else:  # light - clinical white
        bg_primary = "#FFFFFF"
        bg_secondary = "#F8FAFC"
        bg_card = "#FFFFFF"
        text_primary = "#0F172A"
        text_secondary = "#64748B"
        border_color = "#E2E8F0"
        accent_color = "#14B8A6"     # Medical Teal
        accent_secondary = "#3B82F6" # Bioscience Blue
        success_color = "#10B981"
        warning_color = "#F59E0B"
        error_color = "#EF4444"

    st.markdown(f"""
    <style>
        /* Import fonts: Inter for UI + JetBrains Mono for data/code */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* Global Styles - Clinical Dark Mode */
        * {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        /* Monospace for data, code, metrics */
        code, pre, .metric-value, .data-display {{
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        }}

        /* Remove default padding */
        .main {{
            background: {bg_primary};
            padding: 0;
        }}

        .block-container {{
            padding-top: 0;
            padding-bottom: 2rem;
            max-width: 100%;
        }}

        /* Top Navigation Bar - Clinical precision */
        .top-nav {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: {bg_secondary};
            padding: 1rem 3rem;
            border-bottom: 2px solid {accent_color};
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 0;
        }}

        .synthlab-logo {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {accent_color};
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-family: 'JetBrains Mono', monospace;
        }}

        .synthlab-tagline {{
            font-size: 0.75rem;
            color: {text_secondary};
            margin-left: 1rem;
            font-weight: 400;
        }}

        .nav-menu {{
            display: flex;
            gap: 2rem;
            align-items: center;
        }}

        .nav-link {{
            color: {text_secondary};
            font-size: 0.95rem;
            font-weight: 500;
            text-decoration: none;
            transition: color 0.2s;
            cursor: pointer;
        }}

        .nav-link:hover {{
            color: {text_primary};
        }}

        /* Clean buttons */
        .clean-button {{
            padding: 0.625rem 1.25rem;
            border-radius: 8px;
            border: 1px solid {border_color};
            background: {bg_card};
            color: {text_primary};
            font-weight: 500;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .clean-button:hover {{
            background: {bg_secondary};
            border-color: {text_secondary};
        }}

        .primary-button {{
            background: {accent_color};
            color: white;
            border-color: {accent_color};
        }}

        .primary-button:hover {{
            background: #2563eb;
            border-color: #2563eb;
        }}

        /* Sidebar - Clinical precision panel */
        [data-testid="stSidebar"] {{
            background: {bg_secondary};
            border-right: 2px solid {accent_color};
            box-shadow: 4px 0 20px rgba(20, 184, 166, 0.2);
            padding-top: 0;
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background: {bg_secondary};
        }}

        [data-testid="stSidebar"] .stMarkdown {{
            color: {text_primary};
        }}

        [data-testid="stSidebar"] label {{
            color: {text_secondary} !important;
            font-weight: 600;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        [data-testid="stSidebar"] h3 {{
            color: {accent_color};
            font-size: 0.9rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* Streamlit buttons - Clinical precision */
        .stButton > button {{
            background: {accent_color};
            color: {bg_primary};
            border: none;
            border-radius: 6px;
            padding: 0.75rem 1.75rem;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 20px rgba(20, 184, 166, 0.4);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stButton > button:hover {{
            background: {accent_secondary};
            box-shadow: 0 0 25px rgba(59, 130, 246, 0.6);
            transform: translateY(-1px);
        }}

        /* Clean cards */
        .clean-card {{
            background: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            transition: box-shadow 0.2s;
        }}

        .clean-card:hover {{
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        }}

        /* Metric cards - Data-forward with glass morphism */
        .metric-card {{
            background: rgba(51, 65, 85, 0.5);
            backdrop-filter: blur(10px);
            border: 1px solid {border_color};
            border-left: 3px solid {accent_color};
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .metric-card:hover {{
            border-left-color: {accent_secondary};
            box-shadow: 0 8px 16px rgba(20, 184, 166, 0.2);
            transform: translateY(-2px);
        }}

        .metric-value {{
            font-size: 2.25rem;
            font-weight: 600;
            color: {accent_color};
            margin: 0.5rem 0;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: -1px;
        }}

        .metric-label {{
            font-size: 0.7rem;
            font-weight: 600;
            color: {text_secondary};
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}

        .metric-delta {{
            font-size: 0.8rem;
            color: {text_secondary};
            margin-top: 0.5rem;
            font-family: 'JetBrains Mono', monospace;
        }}

        /* Info boxes - Clinical color-coded alerts */
        .info-box {{
            background: rgba(59, 130, 246, 0.1);
            border-left: 4px solid {accent_secondary};
            border-radius: 6px;
            padding: 1rem 1.5rem;
            color: {text_primary};
            margin: 1rem 0;
            font-size: 0.9rem;
            backdrop-filter: blur(5px);
        }}

        .success-box {{
            background: rgba(16, 185, 129, 0.15);
            border-left-color: {success_color};
            color: {text_primary};
        }}

        .warning-box {{
            background: rgba(245, 158, 11, 0.15);
            border-left-color: {warning_color};
            color: {text_primary};
        }}

        .error-box {{
            background: rgba(239, 68, 68, 0.15);
            border-left-color: {error_color};
            color: {text_primary};
        }}

        /* Tabs - Clinical precision with glow */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.25rem;
            background: {bg_secondary};
            margin-bottom: 2rem;
            border-bottom: 2px solid {border_color};
            padding: 0.5rem;
            border-radius: 6px 6px 0 0;
        }}

        .stTabs [data-baseweb="tab"] {{
            background: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            padding: 0.75rem 1.5rem;
            color: {text_secondary};
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.3s;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            color: {accent_color};
            background: rgba(20, 184, 166, 0.1);
        }}

        .stTabs [aria-selected="true"] {{
            color: {accent_color};
            border-bottom-color: {accent_color};
            background: rgba(20, 184, 166, 0.15);
            box-shadow: 0 0 15px rgba(20, 184, 166, 0.3);
        }}

        /* File uploader - Clinical precision */
        [data-testid="stFileUploader"] {{
            background: rgba(51, 65, 85, 0.3);
            border: 2px dashed {accent_color};
            border-radius: 8px;
            padding: 2.5rem;
            transition: all 0.3s;
            backdrop-filter: blur(5px);
        }}

        [data-testid="stFileUploader"]:hover {{
            border-color: {accent_secondary};
            background: rgba(59, 130, 246, 0.1);
            box-shadow: 0 0 20px rgba(20, 184, 166, 0.3);
        }}

        /* Dataframe - Data-forward monospace */
        .dataframe {{
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid {border_color};
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }}

        .dataframe th {{
            background: {bg_secondary};
            color: {accent_color};
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }}

        .dataframe td {{
            background: {bg_card};
            color: {text_primary};
        }}

        /* Progress bar - Clean accent */
        .stProgress > div > div {{
            background: {accent_color};
        }}

        /* Expander - Clean */
        .streamlit-expanderHeader {{
            background: {bg_card};
            border-radius: 8px;
            font-weight: 500;
            color: {text_primary};
            border: 1px solid {border_color};
        }}

        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Text colors */
        h1, h2, h3, h4, h5, h6 {{
            color: {text_primary};
            font-weight: 700;
        }}

        p, span, div {{
            color: {text_primary};
        }}

        /* Inputs - Clean minimal */
        input, textarea, select {{
            background: {bg_card} !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            border-radius: 8px !important;
            font-size: 0.95rem !important;
        }}

        input:focus, textarea:focus, select:focus {{
            border-color: {accent_color} !important;
            outline: none !important;
        }}

        /* Sliders - Clean accent */
        .stSlider > div > div > div {{
            background: {accent_color} !important;
        }}

        /* Spacing adjustments */
        .element-container {{
            margin-bottom: 0.5rem;
        }}

        /* Content container */
        .content-wrapper {{
            padding: 2rem 3rem;
            max-width: 1400px;
            margin: 0 auto;
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
        'theme': 'dark',  # Clinical Dark Mode as default
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
# CLEAN COMPONENTS
# ============================================================================

def render_top_nav():
    """Render clinical dark mode navigation"""

    theme_emoji = "🌙" if st.session_state.theme == 'light' else "☀️"

    st.markdown(f"""
    <div class="top-nav">
        <div style="display: flex; align-items: center;">
            <div class="synthlab-logo">
                <span>🧬</span>
                <span>SynthLab</span>
            </div>
            <span class="synthlab-tagline">Synthetic Healthcare Data. Mathematically Validated.</span>
        </div>
        <div class="nav-menu">
            <span class="nav-link">Generate</span>
            <span class="nav-link">Privacy</span>
            <span class="nav-link">Documentation</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle button
    cols = st.columns([8, 1])
    with cols[1]:
        if st.button(theme_emoji, key="theme_toggle", help="Toggle theme"):
            st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
            st.rerun()


def render_metric_card(label: str, value: str, delta: Optional[str] = None):
    """Render clean metric card"""

    delta_html = f"<div class='metric-delta'>{delta}</div>" if delta else ""

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_info_box(text: str, type: str = "info"):
    """Render clean info box"""
    st.markdown(f'<div class="{type}-box">{text}</div>', unsafe_allow_html=True)


# ============================================================================
# LOGIN PAGE
# ============================================================================

def render_login_page():
    """Clinical dark mode login page"""

    apply_custom_css(st.session_state.theme)

    # Center content
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem;">
            <div style="font-size: 4rem; font-weight: 700; color: #14B8A6; margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace;">
                🧬 SynthLab
            </div>
            <div style="font-size: 1.2rem; color: #94A3B8; font-weight: 500;">
                Synthetic Healthcare Data. Mathematically Validated.
            </div>
            <div style="font-size: 0.9rem; color: #64748B; margin-top: 0.5rem;">
                CTGAN • TVAE • GaussianCopula
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="clean-card">', unsafe_allow_html=True)

        st.markdown("### Welcome Back")
        st.markdown("Sign in to continue")
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")

            st.markdown("<br>", unsafe_allow_html=True)

            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                if username and password:
                    with st.spinner("Authenticating..."):
                        if login(username, password):
                            st.success("✓ Welcome to SynthLab")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                else:
                    st.warning("Please enter both username and password")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        render_info_box("""
        <strong>Default Credentials:</strong><br>
        Username: <code>admin</code> | Password: <code>changeme123</code>
        """, "info")


# ============================================================================
# SIDEBAR
# ============================================================================

def render_sidebar():
    """Render clean minimal sidebar"""

    with st.sidebar:
        user = st.session_state.user_info

        # User profile
        st.markdown(f"""
        <div class="clean-card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 0.75rem;">👤</div>
            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">{user['username']}</div>
            <div style="font-size: 0.85rem; color: #6b7280;">{user['role'].title()}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Sign Out", use_container_width=True):
            logout()

        st.markdown("---")

        # Synthesis Settings
        st.markdown("### ⚙️ Settings")

        method = st.selectbox(
            "Method",
            options=["CTGAN", "GaussianCopula", "TVAE"],
            help="Choose synthesis algorithm"
        )

        num_rows = st.slider(
            "Rows to Generate",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100
        )

        st.markdown("---")

        # Privacy Controls
        st.markdown("### 🔒 Privacy")

        enable_dp = st.toggle(
            "Differential Privacy",
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

            # Privacy level indicator
            if epsilon <= 0.5:
                level, color = "Very Strong", "#22c55e"
            elif epsilon <= 1.0:
                level, color = "Strong", "#3b82f6"
            else:
                level, color = "Moderate", "#f59e0b"

            st.markdown(f"""
            <div style="background: {color}20; color: {color}; padding: 0.625rem;
                        border-radius: 8px; text-align: center; margin-top: 0.75rem;
                        font-weight: 500; font-size: 0.85rem; border: 1px solid {color}40;">
                {level} Privacy
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Advanced Privacy
        with st.expander("Advanced Privacy"):
            k = st.number_input("k-anonymity", 2, 20, st.session_state.privacy_settings['k_anonymity'])
            st.session_state.privacy_settings['k_anonymity'] = k

            l = st.number_input("l-diversity", 2, 10, st.session_state.privacy_settings['l_diversity'])
            st.session_state.privacy_settings['l_diversity'] = l

            t = st.slider("t-closeness", 0.1, 0.5, float(st.session_state.privacy_settings['t_closeness']), 0.05)
            st.session_state.privacy_settings['t_closeness'] = t

        enable_constraints = st.toggle(
            "Constraints",
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

    # Main content wrapper
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

    # Main content tabs - Include Literature tab
    tabs = st.tabs(["Generate", "Privacy Analysis", "Literature", "Cache", "Users" if st.session_state.user_info['role'] == 'admin' else "Docs"])

    # TAB 1: GENERATE
    with tabs[0]:
        st.markdown("### Upload Dataset")

        uploaded_file = st.file_uploader(
            "Drop CSV file here or click to browse",
            type=["csv"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            df = pd.read_csv(uploaded_file)

            # Stats
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
            with st.expander("Preview Data", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            # Generate
            if st.button("Generate Synthetic Data", use_container_width=True, type="primary"):
                with st.spinner("Creating synthetic data..."):
                    try:
                        # Lazy import modules when needed
                        from src.modules.data_loader import DataLoader
                        from src.modules.synthesizer import SyntheticGenerator
                        from src.modules.privacy_engine import DifferentialPrivacyEngine
                        from src.modules.constraint_manager import ConstraintManager

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

                        render_info_box(f"✓ Successfully generated {len(synthetic_data):,} synthetic rows", "success")
                        st.rerun()

                    except Exception as e:
                        render_info_box(f"✗ Error: {str(e)}", "error")

            # Results
            if uploaded_file.name in st.session_state.result:
                result = st.session_state.result[uploaded_file.name]
                synthetic_data = result['synthetic_data']
                clean_df = result['clean_data']

                st.markdown("---")
                st.markdown("### Results")

                # Lazy import
                from src.modules.stress_test import QualityReport

                quality_report = QualityReport(clean_df, synthetic_data)
                privacy_check = quality_report.check_privacy()
                dcr = quality_report.distance_to_closest_record()

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    render_metric_card(
                        "Privacy Score",
                        f"{100 - privacy_check['leaked_percentage']:.0f}%",
                        "No leaks" if privacy_check['leaked_rows'] == 0 else f"{privacy_check['leaked_rows']} leaks"
                    )

                with col2:
                    render_metric_card(
                        "Mean DCR",
                        f"{dcr['mean_distance']:.3f}",
                        "Good" if dcr['mean_distance'] > 0.1 else "Low"
                    )

                with col3:
                    dp_enabled = st.session_state.privacy_settings['enable_dp']
                    render_metric_card(
                        "Diff Privacy",
                        "ON" if dp_enabled else "OFF",
                        f"ε={st.session_state.privacy_settings['epsilon']}" if dp_enabled else "Disabled"
                    )

                with col4:
                    render_metric_card(
                        "Generated",
                        f"{len(synthetic_data):,}",
                        method
                    )

                with st.expander("View Synthetic Data"):
                    st.dataframe(synthetic_data.head(20), use_container_width=True)

                csv = synthetic_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Synthetic Data (CSV)",
                    data=csv,
                    file_name=f'synthetic_{uploaded_file.name}',
                    mime='text/csv',
                    use_container_width=True
                )

    # TAB 2: PRIVACY
    with tabs[1]:
        st.markdown("### Privacy Analysis")

        if not st.session_state.result:
            render_info_box("Generate synthetic data first to access privacy analysis", "info")
        else:
            dataset_name = st.selectbox("Select Dataset", list(st.session_state.result.keys()))

            if dataset_name:
                result = st.session_state.result[dataset_name]
                clean_df = result['clean_data']
                synthetic_df = result['synthetic_data']

                # Lazy import
                from src.modules.stress_test import QualityReport

                quality_report = QualityReport(clean_df, synthetic_df)
                privacy_check = quality_report.check_privacy()
                dcr = quality_report.distance_to_closest_record()

                col1, col2, col3 = st.columns(3)

                with col1:
                    render_metric_card(
                        "Privacy Score",
                        f"{100 - privacy_check['leaked_percentage']:.1f}%",
                        f"{privacy_check['leaked_rows']} exact matches"
                    )

                with col2:
                    render_metric_card(
                        "Mean DCR",
                        f"{dcr['mean_distance']:.4f}",
                        f"Min: {dcr['min_distance']:.4f}"
                    )

                with col3:
                    render_metric_card(
                        "Too Close",
                        f"{dcr['too_close_percentage']:.1f}%",
                        f"{dcr['close_records']} records"
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### Recommendations")

                if privacy_check['leaked_rows'] == 0 and dcr['mean_distance'] > 0.1:
                    render_info_box("✓ Excellent privacy - No exact matches and good separation", "success")
                elif privacy_check['leaked_rows'] > 0:
                    render_info_box(f"⚠ Risk detected - {privacy_check['leaked_rows']} exact matches found. Enable differential privacy", "error")
                else:
                    render_info_box("⚠ Low DCR - Some records are too similar. Consider adjusting parameters", "warning")

    # TAB 3: LITERATURE
    with tabs[2]:
        st.markdown("### Literature Search")

        if LITERATURE_AVAILABLE:
            query = st.text_input("Search for papers related to synthetic data", placeholder="e.g., differential privacy, CTGAN, GAN-based synthesis")

            if st.button("Search Papers"):
                if query:
                    with st.spinner("Searching literature..."):
                        # Lazy import
                        from src.modules.literature import LiteratureSearch

                        if st.session_state.literature_search is None:
                            st.session_state.literature_search = LiteratureSearch()

                        results = st.session_state.literature_search.search(query, max_results=10)

                        if results:
                            render_info_box(f"✓ Found {len(results)} papers", "success")

                            for i, paper in enumerate(results, 1):
                                st.markdown(f"""
                                <div class="clean-card">
                                    <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.5rem;">
                                        {i}. {paper['title']}
                                    </div>
                                    <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem;">
                                        <strong>Authors:</strong> {paper['authors']}
                                    </div>
                                    <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.75rem;">
                                        <strong>Published:</strong> {paper['published']} | <strong>Citations:</strong> {paper.get('citations', 'N/A')}
                                    </div>
                                    <div style="font-size: 0.9rem; margin-bottom: 0.75rem;">
                                        {paper['summary']}
                                    </div>
                                    <a href="{paper['url']}" target="_blank" style="color: #3b82f6; text-decoration: none; font-size: 0.9rem;">
                                        → Read full paper
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown("<br>", unsafe_allow_html=True)
                        else:
                            render_info_box("No papers found. Try a different query.", "info")
                else:
                    st.warning("Please enter a search query")
        else:
            render_info_box("Literature search is not available. Install required dependencies: `pip install arxiv scholarly`", "warning")

    # TAB 4: CACHE
    with tabs[3]:
        st.markdown("### Model Cache")

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
                render_info_box("No cached models yet", "info")
        else:
            render_info_box("Cache will be created on first generation", "info")

    # TAB 5: USERS/DOCS
    with tabs[4]:
        if st.session_state.user_info['role'] == 'admin':
            st.markdown("### User Management")

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
                            render_info_box(f"✓ User created: {new_username}<br>API Key: <code>{user_data['api_key']}</code>", "success")
                        else:
                            render_info_box(f"✗ Error: {response.json().get('detail')}", "error")
                    except Exception as e:
                        render_info_box(f"✗ Error: {str(e)}", "error")
        else:
            st.markdown("### Documentation")
            render_info_box("""
            <strong>Quick Start:</strong><br>
            1. Upload CSV in Generate tab<br>
            2. Configure privacy settings in sidebar<br>
            3. Click Generate<br>
            4. Analyze privacy metrics
            """, "info")

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
