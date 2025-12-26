# Data Editor 复选框修复 - 快速参考

## 修复内容

**文件**：`ui/pages/phase0_expansion.py`

**修改行数**：
- 第 926-937 行：简化主流程状态管理
- 第 1020-1056 行：优化 fragment 内部状态初始化逻辑

## 核心改进

### Before (问题代码)
```python
# Fragment 内部：每次 rerun 都恢复状态
if 'last_edited_df' in st.session_state:
    # 使用旧状态，覆盖用户的新点击 ❌
    last_selection = st.session_state.last_edited_df.set_index('Token')['选择'].to_dict()
    df_with_selection.insert(0, '选择', ...)
```

### After (修复代码)
```python
# Fragment 内部：只在必要时初始化
needs_init = (
    'last_edited_df' not in st.session_state or
    st.session_state.get('force_sync_selection', False)
)

if needs_init:
    # 初始化：使用 session_state ✅
    df_with_selection.insert(0, '选择', ...)
else:
    # 正常点击：使用 last_edited_df 恢复 ✅
    last_selection = st.session_state.last_edited_df.set_index('Token')['选择'].to_dict()
    df_with_selection.insert(0, '选择', ...)
```

## 关键差异

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| **初始化时机** | 每次 rerun | 仅首次/批量操作时 |
| **状态恢复** | 无条件恢复 | 有条件恢复 |
| **状态覆盖** | 会覆盖用户操作 | 不会覆盖 |
| **连续点击** | 第二次会失败 | 正常工作 |

## 测试验证

### 快速测试
```bash
# 1. 启动 Web UI
python -m streamlit run web_ui.py

# 2. 导航到 Phase 0 页面

# 3. 执行分词

# 4. 测试连续点击
#    - 点击 3 个复选框
#    - 应该全部保持选中 ✅
```

### 预期行为
- ✅ 第一次点击：正常
- ✅ 第二次点击：正常（修复前会失败）
- ✅ 第三次点击：正常
- ✅ 批量操作：正常
- ✅ 无闪烁：正常

## 调试技巧

### 开启调试模式
```python
# 在 UI 中勾选 "🐛 开启调试模式"
debug_mode = st.checkbox("🐛 开启调试模式", value=True)
```

### 观察日志
- "✅ 初始化选择列" → needs_init=True
- "✅ 使用last_edited_df恢复状态" → needs_init=False

## 相关文档

- 详细分析：`docs/data_editor_checkbox_fix.md`
- 测试用例：`tests/test_data_editor_checkbox_manual.py`

## 常见问题

### Q1：为什么不完全移除状态恢复逻辑？
A：状态恢复在非初始化时仍然需要，用于保持用户的历史选择。

### Q2：force_sync_selection 的作用是什么？
A：标记批量操作，强制同步 session_state 到 data_editor。

### Q3：last_edited_df 还有用吗？
A：有用！在非初始化时用于恢复状态，确保连续点击的正确性。

### Q4：如果还是有问题怎么办？
A：
1. 开启调试模式，查看日志
2. 检查 needs_init 的判断条件
3. 确认 force_sync_selection 是否正确重置

## 回滚方法

如果修复后出现问题，可以通过 Git 回滚：

```bash
# 查看修改
git diff ui/pages/phase0_expansion.py

# 回滚（如果需要）
git checkout ui/pages/phase0_expansion.py
```

## 性能影响

- ✅ **无性能影响**：只是优化了状态管理逻辑
- ✅ **减少不必要的刷新**：避免每次都重新初始化
- ✅ **提升用户体验**：消除闪烁和状态丢失

## 兼容性

- ✅ Streamlit >= 1.28.0
- ✅ 不影响其他功能
- ✅ 向后兼容

---

**修复日期**：2025-12-25
**修复版本**：v1.0
**状态**：✅ 已测试通过
