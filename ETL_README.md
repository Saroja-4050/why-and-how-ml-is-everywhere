# ETL Pipeline for S2ORC Dataset

## Overview
This ETL pipeline converts S2ORC JSONL.GZ files into optimized Parquet format for high-performance data processing.

**Why Parquet?**
- ✅ Fast: Columnar format optimized for analytics
- ✅ Compressed: Better compression than JSON
- ✅ GPU-ready: cuDF loads Parquet files instantly
- ✅ Type-safe: Preserves data types efficiently

## Installation

### Option 1: Using pip
```bash
pip install pandas pyarrow tqdm
```

### Option 2: Using conda (recommended for RAPIDS/GPU workflows)
```bash
conda install -c conda-forge pandas pyarrow tqdm
```

### Option 3: Install from requirements file
```bash
pip install -r requirements_etl.txt
```

## Usage

### Basic Usage
```bash
python3 etl_pipeline.py
```

### What it does:
1. **Scans** all `.json.gz` and `.jsonl.gz` files in `modular-s2orc-data/` (train, test, and validation)
2. **Extracts** ALL fields with FULL text preservation:
   - Paper ID (required - files without ID are skipped)
   - Year, Fields of study, Full text (100% preserved)
   - Metadata, Attributes, Quality control fields
   - Audit trails (source, created, added, version)
3. **Transforms** data with optimized types
4. **Saves** to Parquet files in `processed_parquet/` directory

### Output Structure
```
processed_parquet/
├── chunk_train_00000.parquet
├── chunk_train_00001.parquet
├── chunk_val_00000.parquet
├── chunk_test_00000.parquet
└── ...
```

## Features

### ✅ Idempotency
- Skips files that have already been processed
- Safe to re-run if interrupted

### ✅ Memory Management
- Processes in chunks (5,000 records at a time)
- Automatic garbage collection
- Handles large files efficiently

### ✅ Error Handling
- Continues processing even if individual records fail
- Reports error counts per file

### ✅ Progress Tracking
- Shows progress bar (if tqdm installed)
- Displays file-by-file status

## Output Schema

Each Parquet file contains:

| Column | Type | Description |
|--------|------|-------------|
| `paper_id` | string | Unique paper identifier |
| `year` | int16 | Publication year |
| `primary_field` | string | Primary field of study |
| `all_fields` | string | All fields (comma-separated) |
| `ext_fields` | string | Extended fields (comma-separated) |
| `citations` | string | Citation IDs (comma-separated) |
| `citation_count` | int16 | Number of citations |
| `text` | string | **FULL TEXT** (100% preserved, no limits) |
| `text_length` | int32 | Full text length |
| `source` | string | Data source (usually "s2") |
| `created` | string | Creation timestamp |
| `added` | string | Addition timestamp |
| `split` | string | train/val/test |
| `source_file` | string | Original filename |

## Loading Parquet Files

### With Pandas (CPU)
```python
import pandas as pd
import glob

# Load all files
files = glob.glob("processed_parquet/*.parquet")
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

# Or load specific split
train_df = pd.read_parquet("processed_parquet/chunk_train_*.parquet")
```

### With cuDF (GPU - RAPIDS)
```python
import cudf
import glob

# Load all files (GPU-accelerated!)
files = glob.glob("processed_parquet/*.parquet")
df = cudf.read_parquet(files)  # Much faster than Pandas!

# Filter by split
train_df = df[df['split'] == 'train']
```

## Performance Tips

1. **Batch Processing**: The script processes in chunks automatically
2. **Parallel Processing**: You can run multiple instances on different directories
3. **Storage**: Parquet files are ~70% smaller than original JSONL.GZ
4. **GPU Acceleration**: Use cuDF for 10-100x faster loading on GPU

## Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"
```bash
pip install pandas pyarrow
```

### Out of Memory
- Reduce `CHUNK_SIZE` in the script (default: 10000)
- Process one split at a time
- Use a machine with more RAM

### Slow Processing
- This is normal for 37GB of data
- Processing ~300 files takes time
- Use SSD storage for better I/O performance

## 📊 Processing Results

### Expected Output
- **Total source files:** ~3,747 files (1,249 train + 1,249 test + 1,249 validation)
- **Processing:** ALL files including validation set
- **Output:** Parquet files in `processed_parquet/` directory

### Known Issues
- **Empty files:** Some test files (677) are empty (44-67 bytes, just gzip headers)
  - These contain no valid data and are correctly skipped
  - This is a data quality issue, not a code bug
- **Train files:** 100% success rate expected
- **Test files:** ~45.8% success rate (due to empty files in source data)

### Logs
- Detailed logs saved to `etl_logs/etl_YYYYMMDD_HHMMSS.log`
- Check logs for processing status and any errors

## Next Steps

After ETL completes:
1. Verify output: `ls -lh processed_parquet/`
2. Check record count: Load a sample file and inspect
3. **Start Jupyter Notebook for analysis:**
   ```bash
   # Make sure you're in the nvidia_impact_env environment
   conda activate nvidia_impact_env
   jupyter lab
   # Or use the helper script:
   ./start_notebook.sh
   ```
4. Open `data_analysis.ipynb` for data exploration and analysis
5. Proceed to Phase 2: Topic Modeling / Classification
