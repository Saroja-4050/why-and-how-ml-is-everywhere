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
1. **Scans** all `.json.gz` and `.jsonl.gz` files in `modded_s2orc_data/s2orc_data/`
2. **Extracts** key fields:
   - Paper ID
   - Year
   - Fields of study
   - Text snippet (first 2000 chars)
   - Citations (if available)
   - Metadata
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
- Processes in chunks (10,000 records at a time)
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
| `text_snippet` | string | First 2000 characters of text |
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

## Next Steps

After ETL completes:
1. Verify output: `ls -lh processed_parquet/`
2. Check record count: Load a sample file and inspect
3. Proceed to Phase 2: Topic Modeling / Classification

## Example: Quick Test

Test on a small subset first:
```bash
# Create test directory with one file
mkdir -p test_data/train
cp modded_s2orc_data/s2orc_data/Economics,2017-2019/train/Economics-2017.gz-0000.json.gz test_data/train/

# Modify SOURCE_ROOT in script temporarily to "test_data"
# Run ETL
python3 etl_pipeline.py
```
