# 🧬 SynthLab

A synthetic data generation platform for healthcare datasets. Generate privacy-safe synthetic data that preserves statistical properties of your original data.

## Features

- **CSV Upload** — Load any tabular dataset
- **Synthetic Generation** — Create fake data using SDV's GaussianCopula
- **Quality Reports** — Compare real vs synthetic statistics
- **Distribution Plots** — Visual comparison with histograms
- **Correlation Analysis** — Heatmaps showing relationship preservation
- **Privacy Check** — Detect if any real rows leaked into synthetic data

## Project Structure
```
SynthLab/
├── app.py                 # Streamlit UI
├── requirements.txt       # Dependencies
├── data/
│   └── raw/              # Original datasets
├── src/
│   └── modules/
│       ├── data_loader.py    # CSV loading & cleaning
│       ├── synthesizer.py    # SDV wrapper
│       └── stress_test.py    # Quality & privacy checks
```

## Test Dataset

Uses the [Pima Indians Diabetes Dataset](https://www.kaggle.com/uciml/pima-indians-diabetes-database) for testing.

## Tech Stack

- Python 3.12
- Streamlit
- SDV (Synthetic Data Vault)
- Pandas
- Plotly

## Roadmap

- [x] Basic synthetic generation
- [x] Quality statistics comparison
- [x] Distribution histograms
- [x] Correlation heatmaps
- [x] Privacy leakage detection
- [ ] Multiple synthesizer options (CTGAN, TVAE)
- [ ] Export quality reports as PDF
