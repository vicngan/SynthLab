cat > README.md << 'EOF'
# 🧬 SynthLab

**A Research Intelligence Platform for Synthetic Data Generation, Quality Validation, and Literature Analysis**

Generate privacy-safe synthetic data that preserves statistical properties while protecting patient privacy. Built for healthcare researchers, data scientists, and clinical AI developers.

## 🚀 Features

### Synthetic Data Engine
- **3 Synthesis Methods**: GaussianCopula, CTGAN, TVAE
- **Medical Constraints**: Automatic bounds enforcement (e.g., Age 0-120, Glucose 0-600)
- **Batch Processing**: Upload multiple CSVs at once

### Quality & Validation
- **Statistical Comparison**: Mean, std, distribution analysis
- **KS Test**: Kolmogorov-Smirnov test for distribution similarity
- **Correlation Heatmaps**: Visual comparison of feature relationships
- **Distribution Histograms**: Side-by-side real vs synthetic plots

### Privacy Analysis
- **Leakage Detection**: Check for exact row matches
- **Distance to Closest Record (DCR)**: Measure re-identification risk
- **Privacy Score**: Quantified privacy assessment

### Fairness Testing
- **Flip Test**: Detect bias by flipping protected attributes
- **Demographic Parity Analysis**: Compare outcomes across groups

### Literature Intelligence (RAG)
- **PDF Upload**: Index research papers
- **Semantic Search**: Find relevant passages by meaning
- **AI Summaries**: Claude-powered answers to research questions

### Export & API
- **PDF Reports**: Download quality reports
- **REST API**: Programmatic access via FastAPI
- **CSV Export**: Download synthetic datasets


## 📁 Project Structure
```
SynthLab/
├── app.py                  # Streamlit UI
├── api.py                  # FastAPI endpoints
├── requirements.txt
├── .env                    # API keys (not tracked)
├── data/
│   ├── raw/               # Original datasets
│   ├── processed/         # Cleaned data
│   └── synthetic/         # Generated data
└── src/
    └── modules/
        ├── data_loader.py    # CSV ingestion & cleaning
        ├── synthesizer.py    # SDV synthesis engine
        ├── stress_test.py    # Quality & privacy metrics
        └── literature.py     # RAG search & summaries
```

## 📊 Supported Metrics

| Metric | Description |
|--------|-------------|
| KS Statistic | Distribution similarity (lower = better) |
| DCR | Distance to closest real record (higher = better) |
| Privacy Score | Overall privacy assessment (0-100) |
| Fairness Score | Bias detection across groups (0-100) |

## 🛣️ Roadmap

- [x] Synthetic Data Engine (CTGAN, TVAE, GaussianCopula)
- [x] Medical Constraints
- [x] Quality Metrics & KS Test
- [x] Privacy Analysis (DCR)
- [x] Fairness Flip Test
- [x] Literature RAG with AI Summaries
- [x] REST API
- [x] PDF Export
- [ ] Streamlit Cloud Deployment
- [ ] Experiment Registry (MLflow)
- [ ] Longitudinal Data Generation

## 📄 License

MIT

## 👩‍💻 Author

**Victoria Nguyen**  

---

*SynthLab: Move Fast and Validate Things™*
EOF