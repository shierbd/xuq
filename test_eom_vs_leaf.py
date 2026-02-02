#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Experiment 2: Testing eom vs leaf for stage 1
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.clustering_service import ClusteringService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./data/products.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def run_test():
    print("="*80)
    print("Experiment 2: Testing eom vs leaf for Stage 1")
    print("="*80)

    db = SessionLocal()

    try:
        print("\nInitializing clustering service...")
        service = ClusteringService(db, model_name="all-mpnet-base-v2")

        print("\nStarting three-stage clustering with eom for Stage 1...")
        print("-"*80)

        result = service.cluster_all_products(
            use_three_stage=True,
            stage1_min_size=10,
            stage2_min_size=5,
            stage3_min_size=3
        )

        print("\n" + "="*80)
        print("CLUSTERING COMPLETED")
        print("="*80)

        print("\nResults:")
        print(f"  Total products: {result['total_products']}")
        print(f"  Clusters: {result['n_clusters']}")
        print(f"  Noise points: {result['n_noise']}")
        print(f"  Noise ratio: {result['noise_ratio']:.2f}%")

        if 'stage_stats' in result:
            print("\nStage breakdown:")
            for stage_name, stats in result['stage_stats'].items():
                print(f"  {stage_name}:")
                print(f"    Clusters: {stats['n_clusters']}")
                print(f"    Noise: {stats['n_noise']}")

        print("\n" + "="*80)
        print("Comparison with previous (leaf for all stages)")
        print("="*80)

        # Previous results (leaf for all stages)
        previous = {
            'total_clusters': 1416,
            'stage1_clusters': 224,
            'stage2_clusters': 462,
            'stage3_clusters': 730,
            'noise': 4645,
            'noise_ratio': 29.41
        }

        print("\nOverall comparison:")
        print(f"  Previous total clusters: {previous['total_clusters']}")
        print(f"  Current total clusters: {result['n_clusters']}")
        print(f"  Difference: {result['n_clusters'] - previous['total_clusters']:+d}")

        print(f"\n  Previous noise: {previous['noise']} ({previous['noise_ratio']:.2f}%)")
        print(f"  Current noise: {result['n_noise']} ({result['noise_ratio']:.2f}%)")
        print(f"  Difference: {result['n_noise'] - previous['noise']:+d}")

        # Analyze results
        print("\n" + "="*80)
        print("Analysis")
        print("="*80)

        cluster_diff = result['n_clusters'] - previous['total_clusters']
        noise_diff = result['n_noise'] - previous['noise']

        if cluster_diff < -100:
            print(f"\n[EXCELLENT] Clusters reduced by {abs(cluster_diff)} ({abs(cluster_diff)/previous['total_clusters']*100:.1f}%)")
            print("  -> eom significantly reduced micro-clusters")
        elif cluster_diff < 0:
            print(f"\n[GOOD] Clusters reduced by {abs(cluster_diff)} ({abs(cluster_diff)/previous['total_clusters']*100:.1f}%)")
            print("  -> eom created more stable clusters")
        elif cluster_diff > 0:
            print(f"\n[UNEXPECTED] Clusters increased by {cluster_diff}")
            print("  -> May need further investigation")
        else:
            print("\n[NEUTRAL] No change in cluster count")

        if noise_diff > 0:
            print(f"\n[EXPECTED] Noise increased by {noise_diff} ({noise_diff/previous['noise']*100:.1f}%)")
            print("  -> eom is more conservative, which is good for theme quality")
        elif noise_diff < 0:
            print(f"\n[GOOD] Noise decreased by {abs(noise_diff)}")
        else:
            print("\n[NEUTRAL] No change in noise")

        print("\n" + "="*80)
        print("Experiment completed successfully")
        print("="*80)

        return result

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        db.close()

if __name__ == "__main__":
    run_test()
