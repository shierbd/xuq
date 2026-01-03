"""检查npz文件的结构"""
import numpy as np
from pathlib import Path

cache_file = Path(r"D:\xiangmu\词根聚类需求挖掘\data\cache\embeddings_round1.npz")

print(f"检查文件: {cache_file}")
print(f"文件大小: {cache_file.stat().st_size / 1024 / 1024:.2f} MB")

data = np.load(cache_file, allow_pickle=True)

print("\n文件中包含的键:")
for key in data.files:
    print(f"  {key}: {data[key].shape if hasattr(data[key], 'shape') else type(data[key])}")
