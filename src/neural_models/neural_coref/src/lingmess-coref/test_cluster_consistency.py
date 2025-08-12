"""
Test script to verify cluster consistency between original and SOTA tokenized data.
"""

import json
from pathlib import Path

def load_jsonlines(file_path):
    """Load JSONL file and return list of documents."""
    documents = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                documents.append(json.loads(line.strip()))
    return documents

def analyze_clusters(documents, name):
    """Analyze cluster statistics for a set of documents."""
    total_docs = len(documents)
    total_clusters = 0
    total_mentions = 0
    doc_cluster_counts = []
    
    for doc in documents:
        clusters = doc.get('clusters', [])
        doc_cluster_count = len(clusters)
        doc_cluster_counts.append(doc_cluster_count)
        total_clusters += doc_cluster_count
        
        # Count total mentions
        for cluster in clusters:
            total_mentions += len(cluster)
    
    avg_clusters = total_clusters / total_docs if total_docs > 0 else 0
    avg_mentions = total_mentions / total_docs if total_docs > 0 else 0
    
    print(f"\n📊 {name} Analysis:")
    print(f"   Total documents: {total_docs}")
    print(f"   Total clusters: {total_clusters}")
    print(f"   Total mentions: {total_mentions}")
    print(f"   Average clusters per doc: {avg_clusters:.2f}")
    print(f"   Average mentions per doc: {avg_mentions:.2f}")
    print(f"   Min clusters per doc: {min(doc_cluster_counts) if doc_cluster_counts else 0}")
    print(f"   Max clusters per doc: {max(doc_cluster_counts) if doc_cluster_counts else 0}")
    
    return {
        'total_docs': total_docs,
        'total_clusters': total_clusters,
        'total_mentions': total_mentions,
        'avg_clusters': avg_clusters,
        'avg_mentions': avg_mentions,
        'doc_cluster_counts': doc_cluster_counts
    }

def compare_documents(original_docs, sota_docs):
    """Compare documents between original and SOTA versions."""
    print("\n🔍 Document Comparison:")
    
    # Create mappings
    original_map = {doc['doc_key']: doc for doc in original_docs}
    sota_map = {doc['doc_key']: doc for doc in sota_docs}
    
    # Find common documents
    common_keys = set(original_map.keys()) & set(sota_map.keys())
    print(f"   Common documents: {len(common_keys)}")
    print(f"   Original only: {len(original_map) - len(common_keys)}")
    print(f"   SOTA only: {len(sota_map) - len(common_keys)}")
    
    # Compare clusters for common documents
    cluster_differences = []
    for doc_key in common_keys:
        original_doc = original_map[doc_key]
        sota_doc = sota_map[doc_key]
        
        original_clusters = original_doc.get('clusters', [])
        sota_clusters = sota_doc.get('clusters', [])
        
        original_count = len(original_clusters)
        sota_count = len(sota_clusters)
        
        if original_count != sota_count:
            cluster_differences.append({
                'doc_key': doc_key,
                'original_clusters': original_count,
                'sota_clusters': sota_count,
                'difference': sota_count - original_count
            })
    
    if cluster_differences:
        print(f"\n⚠️  Found {len(cluster_differences)} documents with cluster count differences:")
        for diff in cluster_differences:
            print(f"   {diff['doc_key']}: {diff['original_clusters']} → {diff['sota_clusters']} ({diff['difference']:+d})")
    else:
        print("\n✅ All common documents have the same cluster count!")
    
    return cluster_differences

def test_cluster_consistency():
    """Test cluster consistency between original and SOTA tokenized data."""
    
    # Load data
    original_file = Path("data/lingmess/hebrew/test.hebrew.jsonlines")
    sota_file = Path("data/lingmess/hebrew/sota_tokenized/test.sota_tokenized_final.jsonlines")
    
    print("Loading data...")
    original_docs = load_jsonlines(original_file)
    sota_docs = load_jsonlines(sota_file)
    
    print(f"✅ Loaded {len(original_docs)} original documents")
    print(f"✅ Loaded {len(sota_docs)} SOTA documents")
    
    # Analyze clusters
    original_stats = analyze_clusters(original_docs, "Original Test Data")
    sota_stats = analyze_clusters(sota_docs, "SOTA Tokenized Data")
    
    # Compare documents
    cluster_differences = compare_documents(original_docs, sota_docs)
    
    # Summary
    print("\n📋 Summary:")
    if cluster_differences:
        print("❌ Cluster count differences detected!")
        print(f"   Documents with differences: {len(cluster_differences)}")
    else:
        print("✅ All documents have consistent cluster counts!")
    
    print(f"\n📈 Cluster Statistics:")
    print(f"   Original total clusters: {original_stats['total_clusters']}")
    print(f"   SOTA total clusters: {sota_stats['total_clusters']}")
    print(f"   Difference: {sota_stats['total_clusters'] - original_stats['total_clusters']:+d}")
    
    # Check if all required fields are present in SOTA data
    print("\n🔍 Field Verification:")
    if sota_docs:
        first_sota_doc = sota_docs[0]
        required_fields = ['doc_key', 'cased_words', 'clusters', 'sent_id', 'pos', 'deprel', 'head', 'part_id', 'sentences', 'speakers']
        missing_fields = [field for field in required_fields if field not in first_sota_doc]
        
        if missing_fields:
            print(f"❌ Missing fields in SOTA data: {missing_fields}")
        else:
            print("✅ All required fields present in SOTA data")
            
            # Verify token alignment
            token_count = len(first_sota_doc['cased_words'])
            field_counts = {
                'sent_id': len(first_sota_doc['sent_id']),
                'pos': len(first_sota_doc['pos']),
                'deprel': len(first_sota_doc['deprel']),
                'head': len(first_sota_doc['head']),
                'speakers': len(first_sota_doc['speakers'])
            }
            
            print(f"   Token count: {token_count}")
            for field, count in field_counts.items():
                status = "✅" if count == token_count else "❌"
                print(f"   {field}: {count} {status}")
    
    return len(cluster_differences) == 0

if __name__ == "__main__":
    success = test_cluster_consistency()
    if success:
        print("\n🎉 All tests passed! Cluster consistency verified.")
    else:
        print("\n⚠️  Some tests failed. Please review the differences.") 