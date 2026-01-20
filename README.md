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

The backend engine provides a robust set of features, all accessible through the new user interface:

### Synthetic Data Engine
- **3 Synthesis Methods**: GaussianCopula, CTGAN, TVAE
- **Medical Constraints**: Automatic bounds enforcement (e.g., Age 0-120, Glucose 0-600)

### Quality & Validation
- **Statistical Comparison**: Mean, std, distribution analysis
- **KS Test**: Kolmogorov-Smirnov test for distribution similarity
- **Correlation Heatmaps**: Visual comparison of feature relationships
- **Distribution Histograms**: Side-by-side real vs synthetic plots

### Privacy Analysis
- **Leakage Detection**: Check for exact row matches
- **Distance to Closest Record (DCR)**: Measure re-identification risk
- **Privacy Score**: Quantified privacy assessment

### Export & API
- **REST API**: Programmatic access to the synthesis engine.
- **JSON Response**: Get synthetic data and all reports in a structured format.

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
