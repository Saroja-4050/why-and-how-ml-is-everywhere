#!/usr/bin/env python3
"""
Monitor ETL pipeline progress
"""

import os
import glob
import time
from datetime import datetime

def monitor_etl():
    """Monitor ETL progress"""
    output_dir = "processed_parquet"
    log_file = "etl_progress.log"
    
    print("="*80)
    print("ETL Pipeline Monitor")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check output directory
    if os.path.exists(output_dir):
        parquet_files = glob.glob(f"{output_dir}/*.parquet")
        total_size = sum(os.path.getsize(f) for f in parquet_files) / (1024*1024)  # MB
        
        print(f"📊 Parquet Files Created: {len(parquet_files)}")
        print(f"💾 Total Size: {total_size:.2f} MB ({total_size/1024:.2f} GB)")
        print()
        
        # Count by split
        train_files = [f for f in parquet_files if 'train' in f]
        val_files = [f for f in parquet_files if 'val' in f]
        test_files = [f for f in parquet_files if 'test' in f]
        
        print(f"   Train: {len(train_files)} files")
        print(f"   Val:   {len(val_files)} files")
        print(f"   Test:  {len(test_files)} files")
        print()
        
        # Show recent files
        if parquet_files:
            print("📁 Most Recent Files:")
            sorted_files = sorted(parquet_files, key=os.path.getmtime, reverse=True)[:5]
            for f in sorted_files:
                size = os.path.getsize(f) / (1024*1024)
                mtime = datetime.fromtimestamp(os.path.getmtime(f))
                print(f"   {os.path.basename(f)}: {size:.1f} MB ({mtime.strftime('%H:%M:%S')})")
    else:
        print("⏳ Output directory not created yet (ETL may be starting...)")
    
    print()
    
    # Check log file
    if os.path.exists(log_file):
        print("📋 Recent Log Activity:")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"   {line.strip()}")
    else:
        print("📋 No log file found yet")
    
    print()
    print("="*80)
    print("To check again, run: python3 monitor_etl.py")
    print("Or watch live: tail -f etl_progress.log")

if __name__ == "__main__":
    monitor_etl()
