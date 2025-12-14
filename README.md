# AI Research Impact Observatory 🔬

A systems engineering pipeline that measures machine learning's real impact on scientific research across disciplines. From raw paper data to interactive dashboards, we quantify adoption patterns, discovery acceleration, and reproducibility trade-offs.

## What It Does

We built a complete data pipeline that:
- **Ingests** scientific papers from S2ORC and validation datasets
- **Classifies** papers by ML adoption level, impact scope, and reproducibility using 4 machine learning models
- **Aggregates** metrics across fields and years to reveal adoption dynamics
- **Visualizes** trends, trade-offs, and insights in an interactive dashboard

The system answers questions like: *Which fields benefit most from ML? Does ML adoption correlate with reproducibility risk? How are adoption patterns evolving over time?*

## Quick Start

For detailed setup instructions, see [SETUP.md](SETUP.md).

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

### Data Pipeline Overview

A modular ETL pipeline following **medallion architecture** (Bronze → Silver → Gold):

```
┌─────────────────────────────────────────────────────────┐
│ BRONZE LAYER: Raw Data Ingestion                        │
│ • 3 datasets: Validation (7,200), ML (3,739), Non-ML   │
│   (25,882) = 36,821 papers total                        │
│ • JSONL → Partitioned Parquet (by field/year)          │
│ • Preserves all original data                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ SILVER LAYER: Feature Engineering & Model Training     │
│ • Label extraction from validation set                  │
│ • Text → Features: HashingVectorizer → TF-IDF → SVD    │
│   (262,144 features → 256 dimensions)                  │
│ • Train 4 ML models on validation set (80/20 split)    │
│ • Apply models to all 36,821 papers                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ GOLD LAYER: Aggregated Metrics & Insights              │
│ • Paper-level scores (ML impact, reproducibility risk) │
│ • Field-year aggregations (trends over time)             │
│ • Field-level rankings (comparisons across disciplines) │
└─────────────────────────────────────────────────────────┘
```

### The Four Machine Learning Models

We train **4 separate classification models** using **Logistic Regression with probability calibration**:

#### 1. **Binary ML Classifier** (`y_is_ml`)
- **Purpose**: Predicts whether a paper uses machine learning (yes/no)
- **Output**: Binary classification (0 = no ML, 1 = uses ML) + confidence score
- **Performance**: 96.5% accuracy, 91.7% macro F1-score
- **Usage**: Filters ML papers and provides probability for composite scoring

#### 2. **ML Adoption Level Classifier** (`y_adoption_level`)
- **Purpose**: Predicts how deeply a paper uses ML
- **Classes**: 5 levels (0=none, 1=minimal, 2=moderate, 3=substantial, 4=core)
- **Output**: Adoption level (0-4) + confidence score
- **Usage**: Measures depth of ML integration (45% weight in ML Impact Score)

#### 3. **Impact Scope Classifier** (`y_impact_scope`)
- **Purpose**: Predicts the potential impact of the research
- **Classes**: 4 levels (0=narrow, 1=moderate, 2=broad, 3=transformative)
- **Output**: Impact level (0-3) + confidence score
- **Usage**: Measures research impact beyond citations (35% weight in ML Impact Score)

#### 4. **Reproducibility Classifier** (`y_reproducibility`)
- **Purpose**: Predicts how feasible it is to reproduce the research
- **Classes**: 4 levels (0=not_feasible, 1=difficult, 2=moderate, 3=straightforward)
- **Output**: Reproducibility level (0-3) + confidence score
- **Usage**: Assesses reproducibility risk (20% weight in ML Impact Score, used for risk calculation)

### Model Training & Data Flow

**Training Phase**:
- **Dataset**: Validation set only (7,200 papers with ground truth labels)
- **Split**: 80% train (5,760 papers) / 20% test (1,440 papers)
- **Process**: Train all 4 models on training set, evaluate on test set
- **Result**: High-performing models ready for prediction

**Prediction Phase**:
- **Datasets**: All 3 datasets (36,821 papers total)
  - Validation set (7,200): Predictions for comparison with ground truth
  - ML unlabeled (3,739): Predictions for papers mentioning ML
  - Non-ML unlabeled (25,882): Predictions for control group
- **Process**: Apply all 4 trained models to generate predictions + confidence scores
- **Output**: Complete predictions for all papers

### Feature Engineering Pipeline

**Text → Numerical Features** (Block 3):

1. **HashingVectorizer**: 
   - Converts words to numerical features using hash functions
   - 262,144 features (2^18), handles infinite vocabulary
   - Uses 1-grams and 2-grams (single words + word pairs)

2. **TF-IDF Transformation**:
   - **TF (Term Frequency)**: How often word appears in paper
   - **IDF (Inverse Document Frequency)**: How rare word is across all papers
   - Gives high weight to distinctive, important words

3. **TruncatedSVD (Dimensionality Reduction)**:
   - Reduces 262,144 features → 256 features
   - Keeps most important patterns, removes noise
   - Makes models train faster while preserving information

**Why this approach?**
- **Scalable**: No vocabulary needed, handles any text
- **Effective**: Captures important words that distinguish papers
- **Efficient**: 256D features train quickly and generalize well

### Interactive Dashboard (`app.py`)

Streamlit app that visualizes:
- **Trends over time**: ML adoption, impact, and reproducibility risk by field
- **Trade-off analysis**: Impact vs. reproducibility risk scatter plots
- **Field leaderboards**: Rankings by ML impact and adoption rates
- **Top papers**: Highest impact papers with detailed metrics
- **Interactive filters**: Field selection, year range, score thresholds

## Datasets

- **Validation**: `modded_s2orc_validation.jsonl` (7,200 labeled papers with ground-truth evaluations)
- **ML Unlabeled**: `modded_s2orc_ml.jsonl` (3,739 papers with ML-related matched terms)
- **Non-ML Unlabeled**: `modded_s2orc_nonml.jsonl` (25,882 papers without ML indicators)

**Total**: 36,821 papers across 56+ scientific fields (2007-2022)

All datasets are partitioned by field and publication year for efficient querying and distributed processing.

## Metrics & Outputs

For detailed formulas and calculations, see [FORMULAS.md](FORMULAS.md).

### Paper-Level Metrics

- **ML Impact Score**: Composite metric (0.0-1.0)
  - **Formula**: `ML_Probability × (0.45 × Adoption_Normalized + 0.35 × Impact_Normalized + 0.20 × Reproducibility_Normalized)`
  - **Weights**: Adoption (45%), Impact (35%), Reproducibility (20%)
  - **Higher = more ML usage + higher impact + better reproducibility**
  
- **Reproducibility Risk Score**: Risk assessment (0.0-1.0)
  - **Formula**: `ML_Probability × (1.0 - Reproducibility_Normalized)`
  - **Higher = higher risk** (ML papers harder to reproduce)

- **Individual Predictions**: Adoption level, impact scope, reproducibility level (with confidence scores)

### Field-Year Metrics

Aggregated by field and publication year:
- `ml_share`: **Formula**: `MEAN(is_ml_prob)` - Percentage of papers using ML (0.0-1.0)
- `avg_ml_impact`: **Formula**: `MEAN(ml_impact_score)` - Average ML impact score
- `avg_repro_risk`: **Formula**: `MEAN(repro_risk)` - Average reproducibility risk
- `p90_ml_impact`, `p99_ml_impact`: **Formula**: `QUANTILE(ml_impact_score, 0.90/0.99)` - Top 10% and 1% impact scores
- `ml_share_yoy`: **Formula**: `ml_share[year] - ml_share[year-1]` - Year-over-year change in ML adoption
- `avg_ml_impact_yoy`: **Formula**: `avg_ml_impact[year] - avg_ml_impact[year-1]` - Year-over-year change in impact

### Field-Level Metrics

Overall field comparisons:
- `ml_share`: **Formula**: `MEAN(is_ml_prob)` - Overall ML adoption rate
- `avg_ml_impact`: **Formula**: `MEAN(ml_impact_score)` - Average impact across all papers
- `p95_ml_impact`: **Formula**: `QUANTILE(ml_impact_score, 0.95)` - 95th percentile impact (top 5% papers)
- `avg_repro_risk`: **Formula**: `MEAN(repro_risk)` - Average reproducibility risk

**Output Files**:
- `gold/paper_scores.parquet`: All paper-level metrics (36,821 rows)
- `gold/field_year_metrics.parquet`: Field-year aggregations
- `gold/field_metrics.parquet`: Field-level summaries

**For detailed formulas and calculation methods, see [FORMULAS.md](FORMULAS.md).**

## Scalability & GPU Acceleration

### Current Implementation

The main pipeline (`main.ipynb`) processes **36,821 papers** on a single machine using:
- **Pandas** (CPU) for data processing
- **scikit-learn** (CPU) for machine learning
- **Parquet** format for efficient storage
- **Streaming ingestion** for memory efficiency

This works efficiently for tens of thousands of papers on standard hardware.

### GPU Acceleration with RAPIDS

The pipeline is designed to leverage **NVIDIA RAPIDS** for GPU-accelerated processing:

**RAPIDS cuDF** (GPU DataFrames):
- Loads Parquet files **10-100x faster** than Pandas
- GPU-accelerated filtering, grouping, and aggregation
- Used in scaling pipelines (`scaling/data_analysis.ipynb`)
- Example: Filtering millions of papers in seconds vs. minutes

**Performance Benefits**:
- **Data loading**: 10-100x faster with cuDF
- **Filtering operations**: GPU parallel processing
- **Aggregations**: Massive speedup for groupby operations
- **Memory efficiency**: GPU memory for large datasets

### Distributed Processing with DGX & Spark

For **enterprise-scale processing** (millions to billions of papers), the infrastructure supports:

#### **NVIDIA DGX Systems**
- Enterprise GPU servers with multiple GPUs (8x A100/H100)
- High-speed interconnects (NVLink, InfiniBand)
- Large GPU memory (hundreds of GB per node)
- Designed for large-scale AI/ML workloads

#### **Apache Spark Integration**
- **Distributed processing**: Spreads work across multiple machines
- **RAPIDS on Spark**: GPU acceleration within Spark workers
- **Fault tolerance**: Automatic recovery from node failures
- **Scalability**: Process datasets that don't fit in single-machine memory

**How It Works**:
```
┌─────────────────────────────────────────────────────┐
│ SPARK CLUSTER (Multiple DGX Nodes)                   │
│                                                      │
│  Node 1 (DGX)      Node 2 (DGX)      Node 3 (DGX)  │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐ │
│  │8x GPUs   │      │8x GPUs   │      │8x GPUs   │ │
│  │RAPIDS    │      │RAPIDS    │      │RAPIDS    │ │
│  │cuDF      │      │cuDF      │      │cuDF      │ │
│  └──────────┘      └──────────┘      └──────────┘ │
│       ↓                  ↓                  ↓        │
│  Process chunk 1    Process chunk 2    Process chunk 3│
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  Spark Coordinator (distributes work)        │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Input: Millions of JSONL.gz files                  │
│  Output: Partitioned Parquet files                  │
└─────────────────────────────────────────────────────┘
```

**Scaling Pipeline** (`scaling/etl_pipeline.py`):
- Designed for Spark distributed ETL
- Converts JSONL.gz → Parquet in parallel across nodes
- Each Spark worker uses RAPIDS cuDF for GPU acceleration
- Handles datasets that don't fit in single-machine memory

**Real-World Scaling Path**:
1. **Current**: Single machine with Pandas (36K papers) ✅ **Demonstrated**
2. **Scale Up**: Single DGX with RAPIDS cuDF (millions of papers)
3. **Scale Out**: Spark cluster with RAPIDS (billions of papers)

**Why This Architecture?**
- **Parquet format**: Works with both Pandas (current) and cuDF (scaling)
- **Partitioning**: Enables parallel processing across nodes
- **Modular design**: Can move from single machine → multi-GPU → distributed cluster
- **Production-ready**: Handles failures, checkpoints, and recovery

## Technical Highlights

- **Scalable architecture**: Partitioned Parquet storage, streaming ingestion, memory-efficient chunking
- **ML pipeline**: Multi-task learning with class-balanced, calibrated classifiers (96%+ accuracy)
- **Feature engineering**: Hashing TF-IDF + TruncatedSVD for high-dimensional text features
- **Production-ready**: Caching layer (SQLite), reproducible runs, comprehensive error handling
- **GPU-ready**: Parquet format compatible with RAPIDS cuDF for accelerated processing
- **Distributed-ready**: Spark integration for cluster-scale processing

## Project Structure

```
.
├── main.ipynb              # Main pipeline (bronze → silver → gold)
├── app.py                  # Streamlit dashboard
├── environment.yml         # Conda environment with RAPIDS, CUDA, etc.
├── SETUP.md                # Detailed setup instructions
├── scaling/                # ETL for larger datasets
│   ├── etl_pipeline.py     # Spark-ready ETL pipeline
│   ├── data_analysis.ipynb  # GPU-accelerated analysis with cuDF
│   └── ETL_README.md       # Scaling documentation
├── modded_s2orc_*.jsonl   # Input datasets
└── observatory_run/        # Pipeline outputs
    ├── data/
    │   ├── bronze/         # Raw partitioned data
    │   ├── silver/         # Labels + predictions
    │   └── gold/           # Aggregated metrics
    └── cache/              # Features + SQLite cache
```

## Future Work

### Short-Term Enhancements
- **Deep learning models**: Experiment with transformer-based models (BERT, SciBERT) for potentially higher accuracy
- **Real-time updates**: Stream processing for new papers as they're published
- **Citation integration**: Incorporate citation networks for impact analysis
- **Author analysis**: Track ML adoption patterns by research groups

### Medium-Term Scaling
- **Multi-GPU training**: Distribute model training across multiple GPUs
- **Incremental learning**: Update models with new data without full retraining
- **Advanced feature engineering**: Incorporate paper metadata, abstracts, figures
- **Ensemble methods**: Combine multiple models for improved predictions

### Long-Term Vision
- **Global observatory**: Process entire S2ORC corpus (200M+ papers)
- **Real-time dashboard**: Live updates as new research is published
- **Predictive analytics**: Forecast ML adoption trends by field
- **Reproducibility scoring**: Automated code/data availability detection
- **Cross-field analysis**: Identify interdisciplinary ML applications

### Infrastructure Improvements
- **Kubernetes deployment**: Containerized pipeline for cloud deployment
- **MLOps integration**: Automated model versioning and deployment
- **Data versioning**: Track dataset versions and model performance over time
- **API endpoints**: RESTful API for programmatic access to metrics

## Why This Matters

Machine learning is transforming science, but quantitative evidence of its impact has been limited. This observatory provides:
- **Data-driven insights** on which disciplines benefit most from ML
- **Reproducibility analysis** to identify potential research quality trade-offs
- **Adoption tracking** to understand how ML techniques spread across fields
- **Impact quantification** beyond citation metrics
- **Scalable infrastructure** ready for enterprise-scale analysis

Built for researchers, policymakers, and anyone curious about AI's role in scientific discovery.

## License

[Add your license here]

## Citation

[Add citation information here]
