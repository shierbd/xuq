"""
Test Stage 2/3 Redesign with Adjusted Parameters (V2)

This script tests the Stage 2/3 redesign with adjusted parameters:
- min_cohesion: 0.5 -> 0.4 (降低)
- min_separation: 0.3 -> 0.15 (大幅降低)
- merge_threshold: 0.5 (保持不变)

Expected results:
- Clusters: 33 -> 100-150 (target: 150-200)
- Noise ratio: 93% -> 40-50%
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
    print_section("STAGE 2/3 REDESIGN TEST V2 - ADJUSTED PARAMETERS")
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

        # Run clustering with adjusted parameters
        print_section("STEP 3: CLUSTERING WITH ADJUSTED PARAMETERS")
        print("\nConfiguration (V2 - Adjusted):")
        print("  - use_merge_strategy: True")
        print("  - stage1_min_size: 10")
        print("  - merge_threshold: 0.5 (unchanged)")
        print("  - min_cohesion: 0.4 (decreased from 0.5)")
        print("  - min_separation: 0.15 (decreased from 0.3)")
        print("  - min_cluster_size: 3")
        print("\nStarting clustering...")

        result = service.cluster_all_products(
            use_three_stage=False,  # Disable old three-stage
            use_merge_strategy=True,  # Enable new merge strategy
            stage1_min_size=10,
            merge_threshold=0.5,
            min_cohesion=0.4,  # Adjusted
            min_separation=0.15,  # Adjusted
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

            # Compare with previous tests
            print_section("COMPARISON WITH PREVIOUS TESTS")

            v1_clusters = 33
            v1_noise = 14700
            phase2_clusters = 1349
            phase2_noise = 4631
            total = 15792

            print("\n| Metric | Phase 2 | V1 (sep=0.3) | V2 (sep=0.15) | V1->V2 Change |")
            print("|--------|---------|--------------|---------------|---------------|")
            print(f"| Clusters | {phase2_clusters} | {v1_clusters} | {result['n_clusters']} | {result['n_clusters']-v1_clusters:+d} |")
            print(f"| Noise | {phase2_noise} ({phase2_noise/total*100:.1f}%) | {v1_noise} ({v1_noise/total*100:.1f}%) | {result['n_noise']} ({result['noise_ratio']:.1f}%) | {result['n_noise']-v1_noise:+d} |")

            # Check if target achieved
            print_section("TARGET ACHIEVEMENT")

            target_min = 150
            target_max = 200
            achieved = target_min <= result['n_clusters'] <= target_max

            print(f"\nTarget: {target_min}-{target_max} clusters")
            print(f"Actual: {result['n_clusters']} clusters")
            print(f"Status: {'[SUCCESS] ACHIEVED' if achieved else '[PARTIAL] NOT FULLY ACHIEVED'}")

            if not achieved:
                if result['n_clusters'] > target_max:
                    print(f"\nNote: Clusters still too many ({result['n_clusters']} > {target_max})")
                    print("Consider:")
                    print("  - Increase merge_threshold (0.5 -> 0.6)")
                    print("  - Increase min_cohesion (0.4 -> 0.5)")
                    print("  - Increase min_separation (0.15 -> 0.2)")
                elif result['n_clusters'] < target_min:
                    print(f"\nNote: Clusters still too few ({result['n_clusters']} < {target_min})")
                    print("Consider:")
                    print("  - Decrease min_cohesion (0.4 -> 0.3)")
                    print("  - Decrease min_separation (0.15 -> 0.1)")
                else:
                    print("\n[SUCCESS] Within acceptable range!")

            # Save results to file
            print_section("STEP 5: SAVING RESULTS")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"docs/实验结果/stage23_redesign_v2_{timestamp}.txt"

            os.makedirs("docs/实验结果", exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("Stage 2/3 Redesign Test Results V2 (Adjusted Parameters)\n")
                f.write("="*80 + "\n\n")
                f.write(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("Configuration V2 (Adjusted):\n")
                f.write("  - use_merge_strategy: True\n")
                f.write("  - stage1_min_size: 10\n")
                f.write("  - merge_threshold: 0.5 (unchanged)\n")
                f.write("  - min_cohesion: 0.4 (decreased from 0.5)\n")
                f.write("  - min_separation: 0.15 (decreased from 0.3)\n")
                f.write("  - min_cluster_size: 3\n\n")

                f.write("Results:\n")
                f.write(f"  - Total products: {result['total_products']}\n")
                f.write(f"  - Total clusters: {result['n_clusters']}\n")
                f.write(f"  - Noise points: {result['n_noise']} ({result['noise_ratio']:.2f}%)\n\n")

                f.write("Comparison:\n")
                f.write(f"  - V1 (sep=0.3): {v1_clusters} clusters, {v1_noise} noise\n")
                f.write(f"  - V2 (sep=0.15): {result['n_clusters']} clusters, {result['n_noise']} noise\n")
                f.write(f"  - Change: {result['n_clusters']-v1_clusters:+d} clusters, {result['n_noise']-v1_noise:+d} noise\n\n")

                f.write("Target Achievement:\n")
                f.write(f"  - Target: {target_min}-{target_max} clusters\n")
                f.write(f"  - Actual: {result['n_clusters']} clusters\n")
                f.write(f"  - Status: {'ACHIEVED' if achieved else 'NOT FULLY ACHIEVED'}\n")

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
