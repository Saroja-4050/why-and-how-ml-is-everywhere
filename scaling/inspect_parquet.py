import pandas as pd
import glob
import os

# CONFIG
OUTPUT_DIR = "processed_parquet"

def inspect_latest_parquet():
    print("--- 🕵️ PARQUET INSPECTION ---")
    
    # 1. Find the latest file
    files = glob.glob(f"{OUTPUT_DIR}/*.parquet")
    if not files:
        print(f"❌ No Parquet files found in {OUTPUT_DIR}. Is ETL running?")
        return

    # Sort by modification time to get the freshest one
    latest_file = max(files, key=os.path.getmtime)
    print(f"📂 Inspecting: {os.path.basename(latest_file)}")
    print(f"   Size: {os.path.getsize(latest_file) / (1024*1024):.2f} MB")

    try:
        # 2. Load Data
        df = pd.read_parquet(latest_file)
        
        # 3. Basic Stats
        print(f"\n📊 Shape: {df.shape} (Rows, Cols)")
        print("\n📋 Columns & Types:")
        print(df.dtypes)

        # 4. Content Peek (The First Row)
        print("\n📝 Sample Record (Row 0):")
        sample = df.iloc[0]
        for col, val in sample.items():
            # Truncate long text for display
            val_str = str(val)
            if len(val_str) > 100:
                val_str = val_str[:100] + "... [TRUNCATED]"
            print(f"   - {col}: {val_str}")

        # 5. Check Critical Fields
        print("\n🔍 Critical Field Check:")
        print(f"   - Has 'year'? {'✅' if 'year' in df.columns else '❌'}")
        print(f"   - Has 'primary_field'? {'✅' if 'primary_field' in df.columns else '❌'}")
        print(f"   - Has 'text'? {'✅' if 'text' in df.columns else '❌'}")
        
        # Check if text is actually populated
        empty_text = df[df['text'] == ""].shape[0]
        print(f"   - Empty Text Rows: {empty_text} / {len(df)}")

    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    inspect_latest_parquet()
