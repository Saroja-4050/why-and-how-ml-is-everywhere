import pandas as pd
import glob
import os

def check_citations():
    print("--- 🕵️ CITATION CONTENT AUDIT ---")
    
    # We grab one Train file (likely to have citations) and one Test file
    train_files = glob.glob("processed_parquet/chunk_train_*.parquet")
    
    if not train_files:
        print("❌ No parquet files found.")
        return

    target_file = train_files[0]
    print(f"📂 Loading: {os.path.basename(target_file)}")
    
    df = pd.read_parquet(target_file)
    
    # 1. Basic Stats
    total = len(df)
    print(f"📊 Total Papers in Chunk: {total}")
    
    # 2. Citation Check (The Critical Part)
    # Filter for non-null, non-empty, non-"[]" citations
    has_cit = df[df['citations'].notna() & (df['citations'] != "") & (df['citations'] != "[]")]
    count = len(has_cit)
    pct = (count / total) * 100
    
    print(f"🔥 Papers with Citations: {count} ({pct:.1f}%)")
    
    if count > 0:
        print("\n✅ SAMPLE CITATIONS (Graph Building is GO):")
        print(has_cit[['paper_id', 'citations']].head(3).to_string(index=False))
        
        # Check density (Average citations per paper)
        # Calculate roughly by splitting string
        avg_cit = has_cit['citations'].str.count(',') + 1
        print(f"\n📈 Avg Citations per Paper: {avg_cit.mean():.1f}")
        
        # Show citation count distribution
        citation_counts = has_cit['citations'].str.count(',') + 1
        print(f"\n📊 Citation Distribution:")
        print(f"   Min: {citation_counts.min()}")
        print(f"   Max: {citation_counts.max()}")
        print(f"   Median: {citation_counts.median():.1f}")
        
    else:
        print("\n❌ NO CITATIONS FOUND.")
        print("   This means we CANNOT build a citation graph.")
        print("   We must pivot to Semantic/Text Analysis immediately.")
    
    # 3. Check across multiple files for consistency
    print("\n" + "="*60)
    print("🔍 CHECKING MULTIPLE FILES FOR CONSISTENCY")
    print("="*60)
    
    sample_files = train_files[:5]  # Check first 5 train files
    total_papers = 0
    total_with_citations = 0
    
    for file in sample_files:
        df_sample = pd.read_parquet(file)
        total_papers += len(df_sample)
        has_cit_sample = df_sample[df_sample['citations'].notna() & 
                                   (df_sample['citations'] != "") & 
                                   (df_sample['citations'] != "[]")]
        total_with_citations += len(has_cit_sample)
    
    overall_pct = (total_with_citations / total_papers * 100) if total_papers > 0 else 0
    print(f"\n📊 Across {len(sample_files)} sample files:")
    print(f"   Total Papers: {total_papers:,}")
    print(f"   Papers with Citations: {total_with_citations:,} ({overall_pct:.1f}%)")
    
    # 4. Check citation_count column if it exists
    if 'citation_count' in df.columns:
        print("\n" + "="*60)
        print("📊 CITATION_COUNT COLUMN ANALYSIS")
        print("="*60)
        non_zero_citations = df[df['citation_count'] > 0]
        print(f"   Papers with citation_count > 0: {len(non_zero_citations)} ({len(non_zero_citations)/total*100:.1f}%)")
        print(f"   Average citation_count (all papers): {df['citation_count'].mean():.1f}")
        print(f"   Average citation_count (papers with citations): {non_zero_citations['citation_count'].mean():.1f}")
    
    # 5. Final Verdict
    print("\n" + "="*60)
    print("🎯 FINAL VERDICT")
    print("="*60)
    
    if total_with_citations > 0:
        print("✅ GO: Citation data is available!")
        print("   → Knowledge Graph strategy is viable")
        print("   → Can build citation networks")
        print(f"   → {overall_pct:.1f}% of papers have citation data")
    else:
        print("❌ NO-GO: No citation data found")
        print("   → Must pivot to Semantic/Text Analysis")
        print("   → Focus on text embeddings and topic modeling")
        print("   → Use field-of-study relationships instead")

if __name__ == "__main__":
    check_citations()
