"""检查npz文件的详细结构"""
import numpy as np
from pathlib import Path

cache_file = Path(r"D:\xiangmu\词根聚类需求挖掘\data\cache\embeddings_round1.npz")

print(f"检查文件: {cache_file}")
print(f"文件大小: {cache_file.stat().st_size / 1024 / 1024:.2f} MB")

data = np.load(cache_file, allow_pickle=True)

print("\n文件中包含的键:")
for key in data.files:
    obj = data[key]
    print(f"\n键: {key}")
    print(f"  类型: {type(obj)}")

    if hasattr(obj, 'shape'):
        print(f"  Shape: {obj.shape}")
        print(f"  Dtype: {obj.dtype}")

    # 如果是字典或可迭代对象
    if isinstance(obj, (dict, np.ndarray)) and obj.shape == ():
        # 尝试获取实际内容
        actual_data = obj.item()
        print(f"  实际类型: {type(actual_data)}")

        if isinstance(actual_data, dict):
            print(f"  字典键: {list(actual_data.keys())}")
            for k, v in actual_data.items():
                if hasattr(v, 'shape'):
                    print(f"    {k}: {v.shape}, dtype={v.dtype}")
                else:
                    print(f"    {k}: {type(v)}, len={len(v) if hasattr(v, '__len__') else 'N/A'}")
