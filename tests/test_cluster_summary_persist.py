import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models.product import Product
from backend.models.product_cluster_keyword import ProductClusterKeyword
from backend.models.product_cluster_summary import ProductClusterSummary
from backend.services.clustering_service import ClusteringService


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


def seed_product(session, product_id, name, cluster_id, cluster_name=None, cluster_name_cn=None):
    session.add(Product(
        product_id=product_id,
        product_name=name,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
        cluster_name_cn=cluster_name_cn,
        is_deleted=False,
        rating=4.5,
        price=9.99,
        review_count=100,
    ))


def test_persist_cluster_summary_ignores_noise():
    session = make_session()
    try:
        seed_product(session, 1, "Noise Product", -1, None, None)
        seed_product(session, 2, "Excel Budget Template", 1, "Excel Template", "Excel ??")
        session.commit()

        session.add_all([
            ProductClusterKeyword(cluster_id=1, keyword="excel", count=10, score=2.0, method="tfidf"),
            ProductClusterKeyword(cluster_id=1, keyword="budget", count=8, score=1.0, method="tfidf"),
        ])
        session.commit()

        result = ClusteringService(session).persist_cluster_summary(top_keywords_limit=2, overwrite=True)
        assert result["success"] is True

        summaries = session.query(ProductClusterSummary).all()
        assert len(summaries) == 1
        assert summaries[0].cluster_id == 1
    finally:
        session.close()


def test_persist_cluster_summary_top_keywords_ordered():
    session = make_session()
    try:
        seed_product(session, 1, "Alpha Report", 2, "Alpha", "Alpha")
        session.commit()

        session.add_all([
            ProductClusterKeyword(cluster_id=2, keyword="alpha", count=5, score=2.0, method="tfidf"),
            ProductClusterKeyword(cluster_id=2, keyword="beta", count=10, score=1.0, method="tfidf"),
            ProductClusterKeyword(cluster_id=2, keyword="gamma", count=9, score=1.0, method="tfidf"),
        ])
        session.commit()

        ClusteringService(session).persist_cluster_summary(top_keywords_limit=2, overwrite=True)

        summary = session.query(ProductClusterSummary).filter_by(cluster_id=2).first()
        assert summary is not None
        assert summary.top_keywords == "alpha, beta"
    finally:
        session.close()
