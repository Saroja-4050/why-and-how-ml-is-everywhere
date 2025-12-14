# AI Research Impact Observatory 🔬

A systems engineering pipeline that measures machine learning's real impact on scientific research across disciplines. From raw paper data to interactive dashboards, we quantify adoption patterns, discovery acceleration, and reproducibility trade-offs.

## What It Does

We built a complete data pipeline that:
- **Ingests** scientific papers from S2ORC and validation datasets
- **Classifies** papers by ML adoption level, impact scope, and reproducibility
- **Aggregates** metrics across fields and years to reveal adoption dynamics
- **Visualizes** trends, trade-offs, and insights in an interactive dashboard

The system answers questions like: *Which fields benefit most from ML? Does ML adoption correlate with reproducibility risk? How are adoption patterns evolving over time?*

## Quick Start

### Setup

```bash
# Create conda environment
conda env create -f environment.yml
conda activate nvidia_impact_env

# Run the pipeline (generates bronze → silver → gold layers)
jupyter lab main.ipynb
# Execute all cells to build the full pipeline

# Launch interactive dashboard
streamlit run app.py
```

## Architecture

### Data Pipeline (`main.ipynb`)

A modular ETL pipeline following medallion architecture:

- **Bronze Layer**: Raw JSONL ingestion → partitioned Parquet (by field/year)
- **Silver Layer**: Label extraction + feature engineering (Hashing TF-IDF → 256D SVD) + ML training (4 classification tasks)
- **Gold Layer**: Aggregated metrics (paper scores, field-year trends, field rankings)

The pipeline trains calibrated logistic regression models to predict:
- ML adoption level (none → core, 5-class)
- Impact scope (narrow → transformative, 4-class)
- Reproducibility feasibility (4-class)
- Binary ML/non-ML classification

### Interactive Dashboard (`app.py`)

Streamlit app that visualizes:
- Adoption S-curves by field over time
- Impact vs. reproducibility risk trade-offs
- Field leaderboards and top papers
- Temporal trends and adoption dynamics

### Scaling (`scaling/`)

ETL pipelines for processing larger S2ORC datasets, converting JSONL.gz to optimized Parquet format for high-performance analytics.

## Datasets

- **Validation**: `modded_s2orc_validation.jsonl` (7,200 labeled papers with ground-truth evaluations)
- **ML Unlabeled**: `modded_s2orc_ml.jsonl` (3,739 papers with ML-related matched terms)
- **Non-ML Unlabeled**: `modded_s2orc_nonml.jsonl` (25,882 papers without ML indicators)

All datasets are partitioned by field and publication year for efficient querying and distributed processing.

## Technical Highlights

- **Scalable architecture**: Partitioned Parquet storage, streaming ingestion, memory-efficient chunking
- **ML pipeline**: Multi-task learning with class-balanced, calibrated classifiers (96%+ accuracy on validation)
- **Feature engineering**: Hashing TF-IDF + TruncatedSVD for high-dimensional text features
- **Production-ready**: Caching layer (SQLite), reproducible runs, comprehensive error handling
- **GPU-ready**: Parquet format compatible with RAPIDS cuDF for accelerated processing

## Output Metrics

- **Paper-level**: ML impact score, reproducibility risk, adoption/impact/repro predictions
- **Field-year**: ML adoption share, average impact, percentiles, year-over-year trends
- **Field-level**: Rankings, adoption rates, impact distributions

## Project Structure

```
.
├── main.ipynb              # Main pipeline (bronze → silver → gold)
├── app.py                  # Streamlit dashboard
├── environment.yml         # Conda environment with RAPIDS, CUDA, etc.
├── scaling/                # ETL for larger datasets
│   ├── etl_pipeline.py
│   └── ETL_README.md
├── modded_s2orc_*.jsonl   # Input datasets
└── observatory_run/        # Pipeline outputs
    ├── data/
    │   ├── bronze/         # Raw partitioned data
    │   ├── silver/         # Labels + predictions
    │   └── gold/           # Aggregated metrics
    └── cache/              # Features + SQLite cache
```

## Why This Matters

Machine learning is transforming science, but quantitative evidence of its impact has been limited. This observatory provides:
- **Data-driven insights** on which disciplines benefit most from ML
- **Reproducibility analysis** to identify potential research quality trade-offs
- **Adoption tracking** to understand how ML techniques spread across fields
- **Impact quantification** beyond citation metrics

Built for researchers, policymakers, and anyone curious about AI's role in scientific discovery.

