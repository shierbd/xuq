"""
Test Stage 2/3 Redesign with Merge Strategy

This script tests the new Stage 2/3 redesign that uses:
- Stage 2: Merge noise points to nearest clusters (don't create new clusters)
- Stage 3: Quality gate (only keep high-quality clusters)

Expected results:
- Clusters: 1,349 -> 150-200 (target)
- Micro clusters: 677 -> 0
- Noise ratio: 29.3% -> 30-40%
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.services.clustering_service import ClusteringService


def print_section(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"[{title}]")
    print("="*80)


def main():
    print_section("STAGE 2/3 REDESIGN TEST")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize database session
    db = SessionLocal()

    try:
        # Initialize clustering service
        print("\n[STEP 1] Initializing clustering service...")
        service = ClusteringService(db)

        # Load model
        print("\n[STEP 2] Loading Sentence Transformer model...")
        service.load_model()
        print("Model loaded successfully!")

        # Run clustering with merge strategy
        print_section("STEP 3: CLUSTERING WITH MERGE STRATEGY")
        print("\nConfiguration:")
        print("  - use_merge_strategy: True")
        print("  - stage1_min_size: 10")
        print("  - merge_threshold: 0.5")
        print("  - min_cohesion: 0.5")
        print("  - min_separation: 0.3")
        print("  - min_cluster_size: 3")
        print("\nStarting clustering...")

        result = service.cluster_all_products(
            use_three_stage=False,  # Disable old three-stage
            use_merge_strategy=True,  # Enable new merge strategy
            stage1_min_size=10,
            merge_threshold=0.5,
            min_cohesion=0.5,
            min_separation=0.3,
            use_cache=True,
            limit=None  # Process all products
        )

        # Print results
        print_section("STEP 4: RESULTS SUMMARY")

        if result.get("success"):
            print("\nClustering completed successfully!")
            print(f"\nTotal products: {result['total_products']}")
            print(f"Total clusters: {result['n_clusters']}")
            print(f"Noise points: {result['n_noise']} ({result['noise_ratio']:.2f}%)")

            # Compare with Phase 2 baseline
            print_section("COMPARISON WITH PHASE 2 BASELINE")

            phase2_clusters = 1349
            phase2_noise = 4631
            phase2_total = 15792

            cluster_reduction = phase2_clusters - result['n_clusters']
            cluster_reduction_pct = cluster_reduction / phase2_clusters * 100

            print("\n| Metric | Phase 2 Baseline | Stage 2/3 Redesign | Change |")
            print("|--------|-----------------|-------------------|--------|")
            print(f"| Total Clusters | {phase2_clusters} | {result['n_clusters']} | {cluster_reduction} ({cluster_reduction_pct:.1f}%) |")
            print(f"| Noise Points | {phase2_noise} ({phase2_noise/phase2_total*100:.1f}%) | {result['n_noise']} ({result['noise_ratio']:.1f}%) | {result['n_noise']-phase2_noise} |")

            # Check if target achieved
            print_section("TARGET ACHIEVEMENT")

            target_min = 150
            target_max = 200
            achieved = target_min <= result['n_clusters'] <= target_max

            print(f"\nTarget: {target_min}-{target_max} clusters")
            print(f"Actual: {result['n_clusters']} clusters")
            print(f"Status: {'✓ ACHIEVED' if achieved else 'X NOT ACHIEVED'}")

            if not achieved:
                if result['n_clusters'] > target_max:
                    print(f"\nSuggestion: Clusters still too many ({result['n_clusters']} > {target_max})")
                    print("Consider:")
                    print("  - Increase merge_threshold (0.5 -> 0.6)")
                    print("  - Increase min_cohesion (0.5 -> 0.6)")
                    print("  - Increase min_separation (0.3 -> 0.4)")
                else:
                    print(f"\nSuggestion: Clusters too few ({result['n_clusters']} < {target_min})")
                    print("Consider:")
                    print("  - Decrease merge_threshold (0.5 -> 0.4)")
                    print("  - Decrease min_cohesion (0.5 -> 0.4)")
                    print("  - Decrease min_separation (0.3 -> 0.2)")

            # Save results to file
            print_section("STEP 5: SAVING RESULTS")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"docs/实验结果/stage23_redesign_{timestamp}.txt"

            os.makedirs("docs/实验结果", exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("Stage 2/3 Redesign Test Results\n")
                f.write("="*80 + "\n\n")
                f.write(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("Configuration:\n")
                f.write("  - use_merge_strategy: True\n")
                f.write("  - stage1_min_size: 10\n")
                f.write("  - merge_threshold: 0.5\n")
                f.write("  - min_cohesion: 0.5\n")
                f.write("  - min_separation: 0.3\n")
                f.write("  - min_cluster_size: 3\n\n")

                f.write("Results:\n")
                f.write(f"  - Total products: {result['total_products']}\n")
                f.write(f"  - Total clusters: {result['n_clusters']}\n")
                f.write(f"  - Noise points: {result['n_noise']} ({result['noise_ratio']:.2f}%)\n\n")

                f.write("Comparison with Phase 2 Baseline:\n")
                f.write(f"  - Cluster reduction: {phase2_clusters} -> {result['n_clusters']} ({cluster_reduction_pct:.1f}%)\n")
                f.write(f"  - Noise change: {phase2_noise} -> {result['n_noise']}\n\n")

                f.write("Target Achievement:\n")
                f.write(f"  - Target: {target_min}-{target_max} clusters\n")
                f.write(f"  - Actual: {result['n_clusters']} clusters\n")
                f.write(f"  - Status: {'ACHIEVED' if achieved else 'NOT ACHIEVED'}\n")

            print(f"\nResults saved to: {output_file}")

        else:
            print(f"\nClustering failed: {result.get('message', 'Unknown error')}")

        print_section("TEST COMPLETED")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    main()
