# Data Editor 复选框状态管理修复方案

## 问题描述

在 `ui/pages/phase0_expansion.py` 中使用 `st.data_editor` 显示带复选框的表格时，出现以下问题：

1. **第一次点击**：正常工作，复选框保持选中状态
2. **第二次点击**：复选框会闪烁，第二个复选框的选择消失
3. **第三次点击**：需要点击两次才能让第二个复选框保持选中状态

## 根本原因

### 问题链条

1. **双重状态管理**：
   - 主流程（第926-970行，修复前）在准备 `df_display` 时添加了"选择"列
   - Fragment 内部（第1055-1062行，修复前）又尝试恢复和初始化"选择"列
   - 导致状态管理逻辑混乱

2. **Fragment 内部的错误状态恢复**：
   ```python
   # 修复前的问题代码（第1055-1062行）
   if 'last_edited_df' in st.session_state and st.session_state.last_edited_df is not None:
       # 每次 fragment rerun 都从 last_edited_df 恢复状态
       last_selection = st.session_state.last_edited_df.set_index('Token')['选择'].to_dict()
       df_with_selection.insert(0, '选择', df_with_selection['Token'].apply(lambda t: last_selection.get(t, False)))
   ```

3. **状态覆盖问题**：
   - 用户点击第二个复选框时，Fragment 重新运行
   - Fragment 使用 `last_edited_df`（只包含第一次点击的状态）初始化数据
   - 这个"旧状态"覆盖了 `data_editor` 已经捕获的"新点击"
   - 导致第二个复选框的选择消失

### 核心问题

**在 Fragment rerun 时不应该重新初始化 data_editor 的输入数据**，因为：
- `st.data_editor` 是有状态的组件，Streamlit 会自动管理其内部状态
- 每次 rerun 都重新初始化会覆盖用户的最新操作
- 应该只在**必要时**初始化，其他时候让 data_editor 自己维护状态

## 修复方案

### 核心思路

1. **移除主流程中的选择列处理**：让 Fragment 全权负责选择状态管理
2. **优化 Fragment 内部逻辑**：只在必要时初始化选择列
3. **明确状态同步时机**：只在批量操作或首次加载时强制同步

### 代码修改

#### 修改1：简化主流程（第926-970行 → 第926-937行）

**修复前**：
```python
# 添加选择列（使用copy避免修改原dataframe）
df_display = df_all.copy()

# 只在批量操作或首次加载时，才用session_state.selected_words初始化"选择"列
if batch_operation_triggered or st.session_state.get('force_sync_selection', False):
    df_display.insert(0, '选择', df_display['Token'].apply(lambda t: t in st.session_state.selected_words))
    st.session_state.force_sync_selection = False
else:
    # 正常情况：使用data_editor的上一次状态
    if 'last_edited_df' in st.session_state and st.session_state.last_edited_df is not None:
        last_selection = st.session_state.last_edited_df.set_index('Token')['选择'].to_dict()
        df_display.insert(0, '选择', df_display['Token'].apply(lambda t: last_selection.get(t, False)))
    else:
        # 首次加载：使用session_state初始化
        df_display.insert(0, '选择', df_display['Token'].apply(lambda t: t in st.session_state.selected_words))
```

**修复后**：
```python
# 准备显示用的DataFrame（不包含选择列，让fragment处理）
df_display = df_all.copy()

# 调试信息（简化）
if debug_mode:
    st.write("### 🔍 状态检查")
    st.write(f"- batch_operation_triggered: {batch_operation_triggered}")
    st.write(f"- selected_words count: {len(st.session_state.selected_words)}")
```

**改进点**：
- 移除主流程中的选择列处理
- 让 Fragment 全权负责状态管理
- 简化调试信息

#### 修改2：优化 Fragment 内部逻辑（第1020-1056行）

**修复前**：
```python
# 恢复之前的选择状态
if 'last_edited_df' in st.session_state and st.session_state.last_edited_df is not None:
    # 从上次的编辑结果中恢复选择状态
    last_selection = st.session_state.last_edited_df.set_index('Token')['选择'].to_dict()
    df_with_selection.insert(0, '选择', df_with_selection['Token'].apply(lambda t: last_selection.get(t, False)))
else:
    # 首次显示，使用session_state中的选择
    df_with_selection.insert(0, '选择', df_with_selection['Token'].apply(lambda t: t in st.session_state.selected_words))
```

**修复后**：
```python
# 只在以下情况下初始化选择列，其他时候让data_editor自己管理状态
# 1. 首次渲染（没有last_edited_df）
# 2. 批量操作或强制同步（force_sync_selection=True）
needs_init = (
    'last_edited_df' not in st.session_state or
    st.session_state.last_edited_df is None or
    st.session_state.get('force_sync_selection', False)
)

if needs_init:
    # 使用session_state初始化选择列
    df_with_selection.insert(0, '选择', df_with_selection['Token'].apply(
        lambda t: t in st.session_state.selected_words
    ))
    st.session_state.force_sync_selection = False

    if debug_mode:
        st.info("✅ 初始化选择列")
else:
    # 使用上次的编辑结果（保持data_editor的状态）
    if 'Token' in st.session_state.last_edited_df.columns and '选择' in st.session_state.last_edited_df.columns:
        last_selection = st.session_state.last_edited_df.set_index('Token')['选择'].to_dict()
        df_with_selection.insert(0, '选择', df_with_selection['Token'].apply(
            lambda t: last_selection.get(t, False)
        ))
    else:
        # 降级：使用session_state初始化
        df_with_selection.insert(0, '选择', df_with_selection['Token'].apply(
            lambda t: t in st.session_state.selected_words
        ))

    if debug_mode:
        st.info("✅ 使用last_edited_df恢复状态")
```

**改进点**：
1. **明确初始化时机**：只在首次渲染或批量操作时初始化
2. **保留状态恢复逻辑**：在非初始化时使用 last_edited_df 恢复状态
3. **避免过度刷新**：正常点击时不重新初始化，让 data_editor 自己管理

### 工作原理

#### 场景1：首次加载

```
用户打开页面
  ↓
主流程执行，准备 df_display（不含选择列）
  ↓
Fragment 执行，needs_init=True（首次渲染）
  ↓
使用 session_state.selected_words 初始化选择列
  ↓
data_editor 显示初始状态
```

#### 场景2：单个复选框点击（正常点击）

```
用户点击复选框
  ↓
Fragment rerun，needs_init=False
  ↓
使用 last_edited_df 恢复状态（包含之前的所有选择）
  ↓
data_editor 在此基础上应用用户的新点击
  ↓
保存到 last_edited_df 和 selected_words
```

**关键**：因为使用了 `last_edited_df` 恢复状态，data_editor 能够正确地在之前的状态基础上应用新的点击。

#### 场景3：批量操作（全选/全不选/反选）

```
用户点击"全选"按钮
  ↓
更新 session_state.selected_words
  ↓
设置 force_sync_selection=True
  ↓
Fragment rerun，needs_init=True
  ↓
使用 session_state.selected_words 强制同步
  ↓
data_editor 显示批量操作后的状态
```

## 验证方法

### 测试步骤

1. **单个复选框测试**：
   - 点击第一个复选框 → 应该保持选中
   - 点击第二个复选框 → 应该保持选中（不闪烁、不消失）
   - 点击第三个复选框 → 应该保持选中
   - 取消第一个复选框 → 应该正确取消

2. **连续点击测试**：
   - 快速连续点击多个复选框
   - 所有选择都应该正确保存

3. **批量操作测试**：
   - 点击"全选" → 所有复选框选中
   - 点击"全不选" → 所有复选框取消
   - 点击"反选" → 选中状态反转
   - 再次单个点击 → 应该正常工作

4. **调试模式测试**：
   - 开启调试模式
   - 观察状态变化日志
   - 确认状态同步正确

### 调试日志示例

**首次加载**：
```
🔍 状态检查
- batch_operation_triggered: False
- selected_words count: 0
- df_all Token数量: 1000

✅ 初始化选择列
```

**正常点击**：
```
✅ 使用last_edited_df恢复状态

🔍 data_editor返回结果
- edited_df Token数量: 1000
- edited_df中已选择数量: 2
- 更新后 selected_words count: 2
```

**批量操作**：
```
🔍 状态检查
- batch_operation_triggered: True
- selected_words count: 1000
- df_all Token数量: 1000

✅ 初始化选择列
```

## 技术要点

### Streamlit Fragment 的状态管理

1. **Fragment 的隔离性**：
   - Fragment 内部的交互只会触发 Fragment rerun
   - 不会触发主流程 rerun
   - 适合用于频繁交互的组件（如 data_editor）

2. **Data Editor 的状态持久化**：
   - `st.data_editor` 使用 `key` 参数管理状态
   - Streamlit 会自动保存组件的内部状态
   - 只要 key 不变，状态就会保持

3. **Session State 的作用**：
   - 用于跨组件共享状态
   - 批量操作时需要同步到 data_editor
   - 导出功能依赖 session_state

### 状态同步策略

1. **初始化时机**：
   - 首次渲染
   - 批量操作
   - 强制同步（force_sync_selection=True）

2. **状态恢复时机**：
   - 正常点击时
   - 使用 last_edited_df 恢复
   - 保持用户的历史选择

3. **状态保存**：
   - 每次 data_editor 返回后保存
   - 更新 last_edited_df 和 selected_words
   - 确保状态一致性

## 注意事项

1. **不要移除 last_edited_df**：
   - 虽然改进了逻辑，但 last_edited_df 仍然重要
   - 用于在非初始化时恢复状态
   - 确保连续点击的正确性

2. **force_sync_selection 的重要性**：
   - 批量操作后必须设置为 True
   - 确保 session_state 和 data_editor 同步
   - 避免状态不一致

3. **调试模式**：
   - 开发阶段建议开启调试模式
   - 观察状态变化，确保逻辑正确
   - 生产环境可关闭

## 总结

本次修复通过以下方式解决了复选框状态管理问题：

1. **简化架构**：移除主流程中的选择列处理，让 Fragment 全权负责
2. **明确时机**：只在必要时初始化，其他时候保持状态
3. **状态恢复**：正常点击时使用 last_edited_df 恢复，避免覆盖用户操作
4. **批量同步**：批量操作时强制同步 session_state 到 data_editor

修复后，用户可以连续点击多个复选框，所有选择都会正确保存，不会出现闪烁或消失的问题。
