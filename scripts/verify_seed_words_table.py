"""验证seed_words表结构"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from storage.models import get_engine
from sqlalchemy import text

engine = get_engine()

with engine.connect() as conn:
    result = conn.execute(text('DESCRIBE seed_words'))
    print('seed_words table structure:')
    print('-' * 100)
    print(f"{'Field':<30} {'Type':<30} {'Null':<10} {'Key':<10} {'Default':<20}")
    print('-' * 100)
    for row in result:
        print(f'{row[0]:<30} {row[1]:<30} {row[2]:<10} {row[3]:<10} {str(row[4]):<20}')
    print('-' * 100)
    print('Table structure verified!')
