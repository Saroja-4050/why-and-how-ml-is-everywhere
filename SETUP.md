# Setup Guide

This guide provides detailed instructions for setting up and running the AI Research Impact Observatory pipeline.

## Prerequisites

- **Conda** (Miniconda or Anaconda) installed
- **Python 3.13** (installed via conda)
- **NVIDIA GPU** (optional, for RAPIDS acceleration)
- **CUDA 13.x** (if using GPU acceleration)
- **8GB+ RAM** (16GB+ recommended)
- **10GB+ disk space** for datasets and outputs

## Environment Setup

### Step 1: Create Conda Environment

The project uses a conda environment with RAPIDS, CUDA, and all required dependencies.

```bash
# Create the environment from environment.yml
conda env create -f environment.yml

# This will install:
# - Python 3.13
# - RAPIDS 25.12 (GPU-accelerated data science)
# - CUDA 13.x (GPU computing)
# - PyArrow 20.0.0 (Parquet processing)
# - JupyterLab, Streamlit, scikit-learn, Pandas, NumPy
# - And all other dependencies
```

### Step 2: Activate Environment

```bash
# Activate the environment
conda activate nvidia_impact_env
```

### Step 3: Verify Installation

```bash
# Verify Python version
python --version  # Should show Python 3.13

# Verify RAPIDS (if using GPU)
python -c "import cudf; print('RAPIDS cuDF available')"

# Verify key packages
python -c "import pandas, numpy, sklearn, streamlit; print('All packages installed')"
```

## Data Preparation

### Step 1: Download Datasets

Place the following JSONL files in the project root directory:

- `modded_s2orc_validation.jsonl` (7,200 papers with labels)
- `modded_s2orc_ml.jsonl` (3,739 papers with ML terms)
- `modded_s2orc_nonml.jsonl` (25,882 papers without ML)

**Expected file structure**:
```
.
├── modded_s2orc_validation.jsonl
├── modded_s2orc_ml.jsonl
├── modded_s2orc_nonml.jsonl
├── main.ipynb
├── app.py
└── ...
```

### Step 2: Verify Data Files

```bash
# Check file sizes (approximate)
ls -lh modded_s2orc_*.jsonl

# Expected sizes:
# - validation: ~50-100 MB
# - ml: ~20-50 MB
# - nonml: ~150-300 MB
```

## Running the Pipeline

### Option 1: Jupyter Notebook (Recommended)

**Step 1: Launch Jupyter Lab**

```bash
# Make sure environment is activated
conda activate nvidia_impact_env

# Launch Jupyter Lab
jupyter lab main.ipynb
```

**Step 2: Execute Blocks Sequentially**

The notebook is organized into 6 blocks. Execute them in order:

1. **Block 0: Configuration & Setup**
   - Creates directories
   - Sets up SQLite cache
   - Configures paths and models
   - ⏱️ Time: ~5 seconds

2. **Block 1: Bronze Layer (Data Ingestion)**
   - Reads JSONL files
   - Converts to partitioned Parquet
   - Organizes by field and year
   - ⏱️ Time: ~2-5 minutes

3. **Block 2: Silver Layer (Label Extraction)**
   - Extracts labels from validation set
   - Creates training targets
   - ⏱️ Time: ~10-30 seconds

4. **Block 3: Feature Engineering**
   - Converts text to features (HashingVectorizer → TF-IDF → SVD)
   - Reduces to 256 dimensions
   - Saves feature matrices
   - ⏱️ Time: ~5-10 minutes

5. **Block 4: Model Training & Prediction**
   - Trains 4 models
   - Evaluates on test set
   - Predicts on all papers
   - ⏱️ Time: ~2-5 minutes

6. **Block 5: Gold Layer (Metrics & Scores)**
   - Calculates paper scores
   - Aggregates by field-year
   - Creates field rankings
   - ⏱️ Time: ~30-60 seconds

7. **Block 6: Visualizations**
   - Generates charts and plots
   - Shows trends and insights
   - ⏱️ Time: ~1-2 minutes

**Total pipeline time**: ~15-25 minutes

### Option 2: Command Line (Advanced)

You can also run individual blocks as Python scripts, but the notebook is recommended for first-time users.

## Running the Dashboard

### Step 1: Ensure Pipeline is Complete

Make sure you've run all blocks in `main.ipynb` and generated the gold layer outputs:
- `observatory_run/data/gold/paper_scores.parquet`
- `observatory_run/data/gold/field_year_metrics.parquet`
- `observatory_run/data/gold/field_metrics.parquet`

### Step 2: Launch Streamlit Dashboard

```bash
# Make sure environment is activated
conda activate nvidia_impact_env

# Launch dashboard
streamlit run app.py
```

### Step 3: Access Dashboard

Open your browser to:
```
http://localhost:8501
```

The dashboard will automatically load the gold layer data and display:
- Key metrics (paper count, average impact, etc.)
- Interactive filters (field, year, score thresholds)
- Trend visualizations
- Field leaderboards
- Top papers table

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError" or Import Errors

```bash
# Make sure environment is activated
conda activate nvidia_impact_env

# Reinstall environment if needed
conda env remove -n nvidia_impact_env
conda env create -f environment.yml
```

#### 2. Out of Memory Errors

- Reduce chunk sizes in Block 1 (currently 2000-8000)
- Close other applications
- Use a machine with more RAM

#### 3. GPU Not Detected (RAPIDS)

```bash
# Check CUDA installation
nvidia-smi

# Verify RAPIDS installation
python -c "import cudf; print(cudf.__version__)"

# If not working, RAPIDS is optional - pipeline works on CPU
```

#### 4. Parquet File Errors

```bash
# Re-run Block 1 to regenerate bronze layer
# Make sure PyArrow is installed
conda install pyarrow=20.0.0
```

#### 5. Dashboard Not Loading Data

```bash
# Check that gold layer files exist
ls -lh observatory_run/data/gold/*.parquet

# If missing, re-run Block 5
```

### Performance Optimization

#### For Faster Processing

1. **Use SSD storage**: Faster I/O for Parquet files
2. **Increase chunk sizes**: If you have more RAM
3. **Use GPU acceleration**: With RAPIDS cuDF (requires GPU)
4. **Parallel processing**: For scaling pipelines

#### For Large Datasets

1. **Use RAPIDS cuDF**: 10-100x faster than Pandas
2. **Distributed processing**: Use Spark with RAPIDS
3. **Incremental processing**: Process in batches
4. **Cloud deployment**: Use GPU instances (AWS, GCP, Azure)

## Environment Details

### Conda Environment File

The `environment.yml` file specifies:

**Channels**:
- `rapidsai`: RAPIDS packages
- `conda-forge`: General packages
- `nvidia`: CUDA drivers

**Key Dependencies**:
- `rapids=25.12`: GPU-accelerated data science
- `python=3.13`: Python version
- `pyarrow=20.0.0`: Parquet processing
- `cuda-version=13.*`: CUDA version
- `jupyterlab`: Notebook environment
- `streamlit`: Dashboard framework
- `scikit-learn`: Machine learning
- `pandas`, `numpy`: Data manipulation

### Installing Additional Packages

```bash
# Activate environment first
conda activate nvidia_impact_env

# Install via conda
conda install package_name

# Or via pip (if not in conda)
pip install package_name
```

## Verification Checklist

Before running the pipeline, verify:

- [ ] Conda environment created and activated
- [ ] All three JSONL datasets in project root
- [ ] Sufficient disk space (10GB+)
- [ ] Sufficient RAM (8GB+ recommended)
- [ ] Jupyter Lab accessible
- [ ] Python 3.13 installed
- [ ] Key packages importable (pandas, numpy, sklearn)

## Next Steps

After setup:

1. **Run the pipeline**: Execute all blocks in `main.ipynb`
2. **Explore the dashboard**: Launch `streamlit run app.py`
3. **Review outputs**: Check `observatory_run/data/gold/` for metrics
4. **Customize**: Modify parameters in Block 0 configuration

For more details, see the main [README.md](README.md).

## Getting Help

- Check the main [README.md](README.md) for architecture details
- Review `DEMO_DOCUMENTATION.md` for comprehensive technical details
- Check `scaling/ETL_README.md` for scaling pipeline information
