"""Check Round 2 import status"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository
from sqlalchemy import func
from storage.models import Phrase

with PhraseRepository() as repo:
    stats = repo.get_statistics()

    print(f"Total records: {stats['total_count']:,}")
    print(f"\nBy round:")
    for round_id, count in stats.get('by_round', {}).items():
        print(f"  Round {round_id}: {count:,}")

    print(f"\nBy source (all data):")
    for source, count in stats.get('by_source', {}).items():
        print(f"  {source}: {count:,}")
