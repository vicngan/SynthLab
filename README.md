# 🧬 SynthLab

**A Research Intelligence Platform for Synthetic Data Generation, Quality Validation, and Literature Analysis**

Generate privacy-safe synthetic data that preserves statistical properties while protecting patient privacy. Built for healthcare researchers, data scientists, and clinical AI developers, now with a full-stack React and Python architecture.

---

## 🏗️ Architecture

SynthLab is now a full-stack application composed of two main parts:

*   **🚀 React Frontend:** The entire user interface is a modern single-page application built with **React** and **Vite**. It provides a fast, interactive experience for uploading data, configuring models, and visualizing results.
*   **🐍 Python Backend:** The core data science engine is powered by a **FastAPI** server. This API exposes the power of the underlying Python libraries for data synthesis, quality analysis, and privacy metrics.

This hybrid model combines the best of both worlds: a rich, responsive user interface and powerful, high-performance data processing.

## ✨ Features

SynthLab provides a robust set of features, all accessible through an intuitive web interface.

### User Interface
- **Interactive Visualization Dashboard**: Automatically generated after each synthesis run, this dashboard provides rich, interactive Plotly charts to visually compare the original and synthetic datasets.
- **Hyperparameter Tuning**: Directly from the UI, you can now configure key model parameters like `Epochs` to fine-tune the performance and quality of the synthesizer (e.g., CTGAN).
- **Tabbed Navigation**: Easily switch between the Data Generator, Literature Review, and Settings modules.
- **Responsive Design**: A clean, modern interface built with TailwindCSS that works on various screen sizes.

### Synthetic Data Engine
- **Multiple Synthesis Methods**: Choose between `CTGAN`, `GaussianCopula`, and `TVAE` synthesizers from the SDV library.
- **Medical Constraints**: Automatic bounds enforcement for common clinical columns (e.g., Age 0-120, Glucose 0-600).

### Quality & Validation
- **Statistical Comparison**: View key descriptive statistics (mean, std, etc.) for both real and synthetic data.
- **Distribution Comparison**: Interactive histograms allow for a side-by-side visual assessment of column distributions.
- **Correlation Heatmaps**: Compare the correlation matrices of the real and synthetic datasets to ensure relationships between variables are preserved.
- **Kolmogorov-Smirnov Test**: Statistical testing for distribution similarity is included in the backend analysis.

### Privacy Analysis
- **Leakage Detection**: Checks for any exact row matches between the real and synthetic data.
- **Distance to Closest Record (DCR)**: A key metric to help measure the risk of re-identification.
- **Differential Privacy (DP) Control**: An `epsilon` parameter is available in the UI as a placeholder for future DP-enabled synthesizer integration.

### Export & API
- **REST API**: Programmatic access to the synthesis engine via FastAPI.
- **JSON Response**: Get synthetic data and all quality/privacy reports in a single structured format.

---

## 🏁 Getting Started

### Prerequisites
*   **Node.js** (v18 or newer) and **npm** for the React frontend.
*   **Python** (v3.9 or newer) and **pip** for the FastAPI backend.

### Installation & Running

The application must be run in two separate terminal sessions: one for the backend and one for the frontend.

**1. Run the Backend API:**
```bash
# Navigate to the project directory
cd /path/to/SynthLab

# (Recommended) Create and activate a Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn api:app --reload
```
The backend will be running at `http://127.0.0.1:8000`.

**2. Run the React Frontend:**
```bash
# In a new terminal, navigate to the same project directory
cd /path/to/SynthLab

# Install JavaScript dependencies
npm install

# Start the React development server
npm start
```
The frontend will automatically open in your browser at `http://localhost:3000`.

---

## 📁 Project Structure
```
SynthLab/
├── api.py                  # FastAPI backend server
├── package.json            # Frontend dependencies
├── vite.config.js          # Frontend build configuration
├── tailwind.config.js      # UI styling configuration
├── requirements.txt        # Backend dependencies
├── index.html              # Main HTML entry point for React
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
└── src/
    ├── App.jsx             # Main React application component
    ├── index.jsx           # React entry point
    ├── components/         # React UI components (Results, etc.)
    └── modules/            # Core Python data science modules
```

## 📄 License

MIT

## 👩‍💻 Author

**Victoria Nguyen**  

---

*SynthLab: Move Fast and Validate Things™*
