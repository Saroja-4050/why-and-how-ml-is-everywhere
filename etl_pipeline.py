#!/usr/bin/env python3
"""
🚀 HYBRID PRODUCTION ETL: S2ORC -> Parquet
Combines "Rich Metadata" extraction with "Systems Engineering" performance.
Extracts ALL fields, preserves FULL text, processes modular-s2orc-data.
"""

import os
import json
import gzip
import glob
import gc
import sys
import time
import logging
from datetime import datetime
import pandas as pd

# --- CONFIGURATION ---
DEFAULT_SOURCE = "modular-s2orc-data"
OUTPUT_DIR = "processed_parquet"
LOG_DIR = "etl_logs"
CHUNK_SIZE = 5000  # Conservative batch size for full-text processing

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --- LOGGING SETUP ---
def setup_logging():
    """Setup comprehensive logging to both file and console"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"etl_{timestamp}.log")
    
    # Create logger
    logger = logging.getLogger('ETL')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers = []
    
    # File handler - detailed logging
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - info and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

# Initialize logging
logger, log_file = setup_logging()

def process_file(file_path, file_index, total_files, split_name=None):
    """Process a single file and convert to Parquet with FULL text + Rich Metadata"""
    
    start_time = time.time()
    
    # Generate Output Filename
    fname = f"chunk_{split_name}_{file_index:05d}.parquet" if split_name else f"chunk_{file_index:05d}.parquet"
    output_path = os.path.join(OUTPUT_DIR, fname)
    
    # 1. IDEMPOTENCY: Skip if already exists
    if os.path.exists(output_path):
        if file_index % 10 == 0: 
            logger.info(f"⏩ Skipping {file_index}/{total_files} (Exists): {os.path.basename(file_path)}")
        return True

    logger.info(f"📄 Processing {file_index}/{total_files}: {os.path.basename(file_path)}...")
    logger.debug(f"   Full path: {file_path}")
    logger.debug(f"   Output: {output_path}")
    
    batch_data = []
    records_processed = 0
    errors = 0
    json_errors = 0
    processing_errors = 0
    
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Fast JSON parse
                    doc = json.loads(line.strip())
                    
                    # --- A. CORE IDENTIFIERS ---
                    paper_id = doc.get('id') or doc.get('paper_id')
                    if not paper_id:
                        errors += 1
                        continue
                    
                    # --- B. RICH METADATA (Complete Extraction) ---
                    meta = doc.get('metadata', {})
                    year = meta.get('year')
                    sha1 = meta.get('sha1')
                    provenance = meta.get('provenance')
                    
                    # Fields of Study (Critical for Graph)
                    fields = meta.get('s2fieldsofstudy', [])
                    primary = fields[0] if fields else 'Unknown'
                    all_fields_str = ','.join(fields) if fields else 'Unknown'
                    ext_fields = meta.get('extfieldsofstudy', [])
                    ext_str = ','.join(ext_fields) if ext_fields else None
                    
                    # --- C. FULL TEXT CONTENT (100% Preservation) ---
                    # Preserving 100% of text for deep learning analysis
                    full_text = doc.get('text', "")
                    text_length = len(full_text)
                    
                    # --- D. AUDIT TRAILS ---
                    # Useful for temporal analysis
                    source = doc.get('source', 'unknown')
                    created = doc.get('created', '')
                    added = doc.get('added', '')
                    version = doc.get('version', '')
                    
                    # --- E. ATTRIBUTES AND QUALITY CONTROL FIELDS ---
                    attributes = doc.get('attributes', {})
                    # Serialize attributes as JSON string to preserve structure
                    attributes_json = json.dumps(attributes) if attributes else None
                    
                    bff_contained_ngram_count = doc.get('bff_contained_ngram_count')
                    bff_duplicate_spans = doc.get('bff_duplicate_spans', [])
                    # Serialize duplicate spans as JSON string
                    bff_duplicate_spans_json = json.dumps(bff_duplicate_spans) if bff_duplicate_spans else None
                    
                    # --- F. BUILD COMPREHENSIVE RECORD ---
                    batch_data.append({
                        'paper_id': str(paper_id),
                        'year': year,
                        'primary_field': primary,
                        'all_fields': all_fields_str,
                        'ext_fields': ext_str,
                        'text': full_text,  # FULL TEXT - NO LIMITS
                        'text_length': text_length,
                        
                        # Metadata Extras
                        'sha1': sha1,
                        'provenance': provenance,
                        'source': source,
                        'created': created,
                        'added': added,
                        'version': version,
                        
                        # Quality Control Fields
                        'attributes': attributes_json,  # Full attributes as JSON string
                        'bff_contained_ngram_count': bff_contained_ngram_count,
                        'bff_duplicate_spans': bff_duplicate_spans_json,  # Full duplicate spans as JSON string
                        
                        # Split info
                        'split': split_name or 'unknown',
                        'source_file': os.path.basename(file_path)
                    })
                    
                    records_processed += 1
                    
                    # Memory Dump if Batch is Full
                    if len(batch_data) >= CHUNK_SIZE:
                        save_batch(batch_data, output_path, append=(records_processed > CHUNK_SIZE))
                        batch_data = []  # Clear memory
                        gc.collect()
                        logger.debug(f"   Batch saved at {records_processed:,} records")
                        
                except json.JSONDecodeError as e:
                    errors += 1
                    json_errors += 1
                    if json_errors <= 5:  # Only log first few errors
                        logger.warning(f"   ⚠️  JSON decode error on line {line_num}: {e}")
                    elif json_errors == 6:
                        logger.warning(f"   ⚠️  (Suppressing further JSON decode errors)")
                    continue
                except Exception as e:
                    errors += 1
                    processing_errors += 1
                    if processing_errors <= 5:
                        logger.warning(f"   ⚠️  Error processing line {line_num}: {e}")
                    elif processing_errors == 6:
                        logger.warning(f"   ⚠️  (Suppressing further processing errors)")
                    continue

        # Save remaining data
        if batch_data:
            save_batch(batch_data, output_path, append=(records_processed > CHUNK_SIZE))
        
        elapsed_time = time.time() - start_time
        
        if records_processed == 0:
            logger.warning(f"⚠️  Warning: No valid data found in {file_path}")
            return False
        
        # Calculate performance metrics
        records_per_sec = records_processed / elapsed_time if elapsed_time > 0 else 0
        
        logger.info(f"   ✅ Saved {records_processed:,} records in {elapsed_time:.2f}s ({records_per_sec:.0f} rec/s)")
        logger.debug(f"   Errors: {errors} (JSON: {json_errors}, Processing: {processing_errors})")
        logger.debug(f"   Output size: {os.path.getsize(output_path) / (1024*1024):.2f} MB" if os.path.exists(output_path) else "   Output size: N/A")
        
        # Aggressive Cleanup
        del batch_data
        gc.collect()
        return True

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ Failed to read file {file_path}: {e}")
        logger.debug(f"   Error after {elapsed_time:.2f}s")
        return False

def save_batch(data, path, append=False):
    """Helper to save DataFrame to Parquet with optimized types"""
    save_start = time.time()
    df = pd.DataFrame(data)
    
    # Type Optimization (Critical for disk usage)
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype('int16')
    if 'text_length' in df.columns:
        df['text_length'] = df['text_length'].astype('int32')
    if 'bff_contained_ngram_count' in df.columns:
        df['bff_contained_ngram_count'] = pd.to_numeric(df['bff_contained_ngram_count'], errors='coerce').fillna(0).astype('int32')
        
    # Write to disk
    if append and os.path.exists(path):
        existing = pd.read_parquet(path)
        df = pd.concat([existing, df], ignore_index=True)
        
    # Snappy compression is the standard for Big Data
    df.to_parquet(path, index=False, compression='snappy', engine='pyarrow')
    
    save_time = time.time() - save_start
    logger.debug(f"   Batch save: {len(data)} records in {save_time:.2f}s")
    
    del df
    gc.collect()

def main():
    pipeline_start = time.time()
    source_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE
    
    logger.info("="*80)
    logger.info(f"🚀 HYBRID PRODUCTION ETL | Target: {source_dir}")
    logger.info(f"💾 Output: {OUTPUT_DIR}")
    logger.info(f"📝 Log file: {log_file}")
    logger.info("="*80)
    logger.debug(f"Configuration:")
    logger.debug(f"  - Source directory: {source_dir}")
    logger.debug(f"  - Output directory: {OUTPUT_DIR}")
    logger.debug(f"  - Chunk size: {CHUNK_SIZE}")
    logger.debug(f"  - Python version: {sys.version}")
    
    # Robust file finding
    logger.info("🔍 Scanning for source files...")
    scan_start = time.time()
    all_files = glob.glob(f"{source_dir}/**/*.json.gz", recursive=True)
    all_files += glob.glob(f"{source_dir}/**/*.jsonl.gz", recursive=True)
    all_files = sorted(list(set(all_files)))
    scan_time = time.time() - scan_start
    logger.debug(f"File scan completed in {scan_time:.2f}s")
    
    # Filter out validation set - only process train and test
    train_files = [f for f in all_files if '/train/' in f]
    test_files = [f for f in all_files if '/test/' in f]
    val_files = [f for f in all_files if '/val/' in f or '/validation/' in f]
    
    files_to_process = train_files + test_files
    
    logger.info(f"📚 Found {len(all_files)} total files:")
    logger.info(f"   Train: {len(train_files)} files")
    logger.info(f"   Val:   {len(val_files)} files (SKIPPING)")
    logger.info(f"   Test:  {len(test_files)} files")
    logger.info(f"   Processing: {len(files_to_process)} files")
    logger.info("")
    
    stats = {'train': 0, 'test': 0, 'failed': 0}
    total_records = 0
    
    logger.info("🚀 Starting file processing...")
    logger.info("")
    
    for i, fpath in enumerate(files_to_process):
        split = 'train' if '/train/' in fpath else 'test'
        success = process_file(fpath, i, len(files_to_process), split_name=split)
        
        if success:
            stats[split] += 1
        else:
            stats['failed'] += 1
        
        # Periodic Garbage Collection and Progress Update
        if i % 5 == 0:
            gc.collect()
            progress = (i + 1) / len(files_to_process) * 100
            logger.info(f"📊 Progress: {i+1}/{len(files_to_process)} files ({progress:.1f}%)")
        
        # Periodic summary every 50 files
        if (i + 1) % 50 == 0:
            elapsed = time.time() - pipeline_start
            logger.info(f"⏱️  Elapsed time: {elapsed/60:.1f} minutes | Processed: {stats['train'] + stats['test']} files")

    pipeline_time = time.time() - pipeline_start
    
    logger.info("")
    logger.info("="*80)
    logger.info("🎉 HYBRID ETL COMPLETE!")
    logger.info("="*80)
    logger.info(f"✅ Train files processed: {stats['train']}")
    logger.info(f"✅ Test files processed:  {stats['test']}")
    if stats['failed'] > 0:
        logger.warning(f"❌ Failed files:         {stats['failed']}")
    logger.info(f"📊 Total files processed: {stats['train'] + stats['test']}")
    logger.info(f"⏱️  Total time: {pipeline_time/60:.1f} minutes ({pipeline_time:.1f} seconds)")
    logger.info(f"💾 Output directory: {OUTPUT_DIR}")
    logger.info(f"📝 Log file: {log_file}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  - Verify Parquet files: ls -lh processed_parquet/")
    logger.info("  - Load with cuDF: import cudf; df = cudf.read_parquet('processed_parquet/*.parquet')")
    logger.info("  - Load with Pandas: import pandas as pd; df = pd.read_parquet('processed_parquet/*.parquet')")
    
    logger.debug("="*80)
    logger.debug("FINAL STATISTICS")
    logger.debug("="*80)
    logger.debug(f"Total execution time: {pipeline_time:.2f} seconds")
    logger.debug(f"Average time per file: {pipeline_time / len(files_to_process):.2f} seconds" if files_to_process else "N/A")
    logger.debug(f"Files processed successfully: {stats['train'] + stats['test']}")
    logger.debug(f"Files failed: {stats['failed']}")
    logger.debug(f"Success rate: {(stats['train'] + stats['test']) / len(files_to_process) * 100:.1f}%" if files_to_process else "N/A")

if __name__ == "__main__":
    main()
