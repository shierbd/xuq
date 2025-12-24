"""
一次性迁移脚本：使用AI重新翻译所有词根
将现有的机器翻译（Google Translate）替换为更准确的AI翻译
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from storage.repository import SeedWordRepository
from storage.word_segment_repository import WordSegmentRepository
from storage.models import WordSegment
from ai.client import LLMClient
from datetime import datetime

def migrate():
    """执行AI翻译迁移"""
    print("="*70)
    print("开始使用AI重新翻译所有词根...")
    print("="*70)

    # 1. 获取所有词根
    print("\n[1/4] 加载所有词根...")
    with SeedWordRepository() as repo:
        all_seeds = repo.get_all_seed_words()

    if not all_seeds:
        print("[ERROR] 没有找到词根数据")
        return

    seed_words = [s.seed_word for s in all_seeds]
    print(f"[OK] 找到 {len(seed_words)} 个词根")

    # 2. 使用AI翻译
    print("\n[2/4] 使用AI翻译词根...")
    print("（这可能需要几分钟，取决于词根数量和API速度）")

    try:
        llm = LLMClient()
        translations = llm.batch_translate_seed_words(seed_words, batch_size=50)
        print(f"[OK] AI翻译完成！成功翻译 {len(translations)} 个词根")
    except Exception as e:
        print(f"[ERROR] AI翻译失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # 3. 保存到数据库
    print("\n[3/4] 保存翻译到数据库...")
    saved_count = 0
    updated_count = 0

    try:
        with WordSegmentRepository() as ws_repo:
            for word, trans in translations.items():
                # 检查是否已存在
                existing = ws_repo.get_word_segment(word)
                if existing:
                    # 更新翻译
                    old_trans = existing.translation
                    existing.translation = trans
                    updated_count += 1

                    # 如果翻译有变化，打印出来
                    if old_trans != trans and old_trans:
                        print(f"  更新: {word}")
                        print(f"    旧翻译: {old_trans}")
                        print(f"    新翻译: {trans}")
                else:
                    # 创建新记录
                    new_ws = WordSegment(
                        word=word,
                        frequency=0,
                        translation=trans,
                        created_at=datetime.utcnow()
                    )
                    ws_repo.session.add(new_ws)
                    saved_count += 1

            ws_repo.session.commit()

        print(f"\n[OK] 保存完成！")
        print(f"  - 新增翻译: {saved_count}")
        print(f"  - 更新翻译: {updated_count}")

    except Exception as e:
        print(f"[ERROR] 保存失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # 4. 验证
    print("\n[4/4] 验证翻译结果...")
    with WordSegmentRepository() as ws_repo:
        verified_count = 0
        for word in seed_words:
            ws = ws_repo.get_word_segment(word)
            if ws and ws.translation:
                verified_count += 1

    print(f"[OK] 验证完成！{verified_count}/{len(seed_words)} 个词根已有翻译")

    # 5. 显示示例
    print("\n" + "="*70)
    print("翻译示例（前10个）：")
    print("="*70)
    count = 0
    with WordSegmentRepository() as ws_repo:
        for word in seed_words[:10]:
            ws = ws_repo.get_word_segment(word)
            if ws and ws.translation:
                print(f"  {word:<20} → {ws.translation}")
                count += 1
                if count >= 10:
                    break

    print("\n" + "="*70)
    print("[OK] 迁移完成！所有词根已使用AI重新翻译")
    print("="*70)

if __name__ == "__main__":
    try:
        migrate()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n[ERROR] 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
