#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test for cosine metric (normalized euclidean)
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
    print("Testing cosine metric (L2 normalization + euclidean)")
    print("="*80)

    db = SessionLocal()

    try:
        print("\nInitializing clustering service...")
        service = ClusteringService(db, model_name="all-mpnet-base-v2")

        print("\nStarting three-stage clustering with normalized embeddings...")
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

        print("\nComparison with previous (euclidean without normalization):")
        print(f"  Previous clusters: 1412")
        print(f"  Current clusters: {result['n_clusters']}")
        print(f"  Difference: {result['n_clusters'] - 1412:+d}")

        print(f"\n  Previous noise: 4620 (29.26%)")
        print(f"  Current noise: {result['n_noise']} ({result['noise_ratio']:.2f}%)")
        print(f"  Difference: {result['n_noise'] - 4620:+d}")

        if result['n_clusters'] < 1412:
            print("\n[GOOD] Fewer clusters - more stable clustering")
        elif result['n_clusters'] > 1412:
            print("\n[NOTE] More clusters - may need parameter adjustment")

        if result['n_noise'] < 4620:
            print("[GOOD] Less noise - better coverage")
        elif result['n_noise'] > 4620:
            print("[NOTE] More noise - more conservative clustering")

        print("\n" + "="*80)
        print("Test completed successfully")
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
