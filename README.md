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
- **Experiment History / Lab Notebook**: For full reproducibility, every synthesis run is saved as an "Experiment." The History tab provides a persistent, browsable log of all previous runs, allowing you to review the exact configuration and visual reports for any experiment at any time.
- **Interactive Visualization Dashboard**: Automatically generated after each synthesis run, this dashboard provides rich, interactive Plotly charts to visually compare the original and synthetic datasets.
- **Clickable Graph Cards**: Distribution plots and correlation heatmaps are displayed as clickable thumbnail cards. Click to expand any graph into a full-size interactive modal.
- **Graph Annotations**: Add persistent notes and comments directly on any graph (similar to Google Docs comments). Annotations are saved per-experiment and displayed as markers on the chart.
- **Hyperparameter Tuning**: Directly from the UI, you can now configure key model parameters like `Epochs` to fine-tune the performance and quality of the synthesizer (e.g., CTGAN).
- **Tabbed Navigation**: Easily switch between the Data Generator, History, Literature Review, and Settings modules.
- **Responsive Design**: A clean, modern interface built with TailwindCSS that works on various screen sizes.

### Synthetic Data Engine
- **Multiple Synthesis Methods**: Choose between `CTGAN`, `GaussianCopula`, `TVAE`, and `PAR` (Probabilistic AutoRegressive) synthesizers from the SDV library.
- **Longitudinal Data Support**: Use the PAR model to synthesize sequential patient data (e.g., multiple visits per patient) while preserving temporal dependencies.
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
- **One-Click Compliance Certificate**: Generate a professional PDF report certifying privacy safety (DCR score) and statistical fidelity for IRB submissions.
- **FHIR Interoperability**: Export synthetic patient cohorts directly to HL7 FHIR R4 JSON format for integration with healthcare systems (Epic/Cerner sandboxes).

### Clinical & BME Specifics
- **Smart Type Detection**: Automatically identifies clinical columns (e.g., HbA1c, Glucose) and suggests appropriate physiological bounds and distributions.
- **ICD-10 Support**: Specialized validation for hierarchical medical codes to ensure synthetic data adheres to standard medical coding formats.

### Literature Intelligence
- **PDF Knowledge Base**: Upload and index research papers (PDFs) to create a searchable local library.
- **Semantic Search**: Use natural language queries to find relevant sections across your uploaded literature.
- **AI Summarization**: Generate summaries of search results to quickly understand the state of the art (requires Anthropic API key).
- **Session Persistence**: Save and load literature review sessions. FAISS indexes, search history, and annotations are preserved to disk for long-term storage.
- **Search History**: Browse previous queries and their results within any saved session.
- **Text Highlighting**: Select and highlight text in search results with color-coded annotations and optional notes.

### Collaboration & Versioning
- **Annotation Layers**: Add Markdown notes to a generation run and place positional annotations directly on graphs for precise commentary.
- **Dataset Forking**: Let a user take an existing synthetic dataset configuration and "branch" it to test a different hypothesis (e.g., "What if we skew the age distribution older?").
- **Version Control**: Automatic saving of data, configurations, and modifications to ensure full reproducibility and lineage tracking.
- **Persistent Storage**: All annotations (graph notes, literature highlights) are stored as JSON files for long-term access across sessions.

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

# (Optional) Create a .env file for API keys
# echo "ANTHROPIC_API_KEY=your_key_here" > .env

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
├── requirements.txt        # Backend dependencies
├── experiments/            # Stores all experiment artifacts for reproducibility
│   └── exp_.../
│       ├── config.json
│       ├── report.json
│       ├── notes.md
│       ├── annotations.json    # Graph annotations (positional notes)
│       └── synthetic_data.csv
├── literature/             # Persistent literature review sessions
│   └── {session_id}/
│       ├── session.json        # Session metadata
│       ├── queries.json        # Search history
│       ├── annotations.json    # Text highlights
│       ├── index.faiss         # FAISS vector index
│       └── documents.pkl       # Document embeddings
├── data/
│   ├── raw/
│   └── synthetic/
└── src/
    ├── App.jsx             # Main React application component
    ├── components/         # React UI components
    │   ├── AnnotationLayer.jsx     # Graph annotation overlay
    │   ├── ComparisonDashboard.jsx # Clickable graph cards + modal
    │   ├── ExperimentDetail.jsx    # Experiment detail view
    │   ├── ExperimentHistory.jsx   # Experiment list
    │   ├── HighlightableText.jsx   # Text highlighting for literature
    │   ├── LiteratureHistory.jsx   # Literature session history
    │   └── Results.jsx             # Tabbed results display
    └── modules/            # Core Python data science modules
```

## 📄 License

MIT

## 👩‍💻 Author

**Victoria Nguyen**  

---

*SynthLab: Move Fast and Validate Things™*
