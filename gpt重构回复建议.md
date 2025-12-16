整体看，这份重构计划已经非常成熟了：目标清晰、步骤分段、风险和回滚都有考虑，而且对自己项目结构和依赖非常熟。更多是「打磨」而不是「推翻重来」。

我按你希望的 5 个维度来审查，并在最后给一个「如果今天就要动手」的简短执行建议。

⸻

1️⃣ 可行性：整体是可执行的，但有几个小坑

✅ 优点（总体是“能落地”的）
	•	步骤顺序基本合理
	•	先备份 + 建 Git 仓库 + 新建重构分支（阶段0）
	•	再从「风险低的文档/目录结构」动手（根目录文档 → docs → data）
	•	然后才改配置和导入路径，最后整体测试
	•	有明确的完成标准
	•	每个阶段都有清晰的“目标”和“预期结果”，最后还有一份完整 checklist，这对控制范围很重要。
	•	路径与文件分类逻辑清晰
	•	data 拆分 raw / processed / results
	•	scripts 拆分 core / tools / selectors / lib
	•	docs 拆分 guides / tutorials / technical / reference / history
这些分类和你当前工作流是对得上的。

⚠️ 需要注意/补充的点
	1.	命令的可执行性（你在 Windows 环境）
	•	tar -czf ...、touch、find 这类命令在 Win 原生 PowerShell / CMD 下是不可用的，属于 类 Unix 指令。
	•	你计划里混用 cd D:\... + tar + touch + find，真实操作时要么：
	•	在 Git Bash / WSL 里整体操作；
	•	要么把这些命令翻译成 PowerShell 版本（例如新建文件用 ni / New-Item）。
👉 建议：在正式执行前，先统一约定“只用 PowerShell”或“只用 Git Bash”，然后把整套命令翻译一遍，避免执行中断。
	2.	pyproject.toml 和实际代码结构没完全对齐
	•	你在 pyproject.toml 里配置了：

[project.scripts]
keyword-mining = "keyword_mining.cli:main"

但当前重构计划里，并没有真正创建 src/keyword_mining/cli.py。

	•	这会导致未来一旦执行 pip install . 或 python -m keyword_mining 很容易炸。
👉 建议：要么暂时不写 [project.scripts]，只保留项目元数据；要么加一个最小的 cli.py stub（哪怕只是打印一句话）。

	3.	“混合方案”的文字 vs 实际执行步骤
	•	文案上你说是「初期方案B、长期演进方案A」，
	•	实际 本次执行计划 完全是方案 B 路线（没有 src/keyword_mining 这层，也没有真正包化）。
👉 这没问题，但建议在文档里明说一句：
“本次重构仅实现方案 B（简化结构），方案 A 留作后续二期重构。”
	4.	导入路径：目前方案是过渡性质
	•	你现在的做法是：

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.config import ...


	•	这在「脚本直跑」的阶段是可行的，但从长期看是一种过渡方案，不是最终形态。
	•	真正的长期方案仍然应该是：
	•	把 scripts/ 变成调用已安装包的“薄壳”；
	•	业务逻辑放到可导入的 package 里（src/keyword_mining/...）。
👉 对现在的你来说，这是可以接受的策略：先确保“能跑”，以后再包化，但要在文档中标记为“过渡方案”。

	5.	测试策略还停留在“手工测试脚本”层面
	•	阶段10的“测试重构后的系统”其实是人工跑每个脚本，这能 catch 大部分路径错误，但：
	•	无法防止回归（未来修改再引入 bug）；
	•	也无法自动对比“重构前后输出有没有差异”。
👉 这里有一个 非常值得加的步骤（见下面第 5 部分细化）。

⸻

2️⃣ 风险评估：分级大体正确，但遗漏了两个重要风险

你现在的风险分级大体 OK，但有几个点值得补充和微调。

✅ 已有风险分级中的优点
	•	把 “导入路径修改” + “数据文件移动” 放在高风险类，这是对的；
	•	有明确的回滚策略（git 分支 + tar 备份）；
	•	中风险里区分了「重命名目录」和「修改配置」；
	•	低风险里把「移动文档 / 新建文件」归类，符合实际。

⚠️ 建议增加/调整的风险点
	1.	遗漏的高风险：输出语义一致性（不只是“能跑”）
	•	目前高风险更多集中在“跑不起来”（ImportError、路径错误）；
	•	但对你这个项目来说，还有一个核心风险：
“重构后 A3 / B3 的聚类结果悄悄发生变化，但你没发现。”
	•	例如：
	•	不小心换了一个预处理参数；
	•	误改了 min_cluster_size / min_samples 的默认值；
	•	换了数据路径导致跑的是「旧数据」。
👉 这类风险应该单独列一条高风险，并加一条缓解措施：
	•	在重构前保存一份「基准输出」（比如某个固定 seed 下的 stageA_clusters.csv + cluster_summary_A3.csv）
	•	重构后对比关键统计指标（簇数、噪声点数量、某几个簇的代表短语等）。
	2.	遗漏的中风险：环境/依赖不一致
	•	你写了 pyproject.toml + requirements.txt，但没有定义“谁是权威来源”。
	•	长期放任的话，可能出现：
	•	本地环境与 requirements.txt 不一致；
	•	别人在新环境中安装后复现不了你的结果。
👉 建议：
	•	明确约定：
	•	短期只维护 requirements.txt 为准；
	•	未来如决定用 pyproject.toml + pip-tools（或 uv/poetry），再切换。
	3.	风险分级微调
	•	「删除空目录和冗余文件」现在被归为低风险，其实有一部分是中风险：
	•	某些“冗余文档”实际上可能还在用（只是你暂时想不起来）；
	•	建议：
	•	删除前先在文档里标注「已归档」，而不是完全删除；
	•	或者先移动到 docs/archive/，观察一段时间再删。

⸻

3️⃣ 方案选择：现在更适合「方案 B + 最小标准化」，方案 A 作为二期

基于你的项目特点：
	•	单人主导开发 + 约 3,500 行 Python；
	•	当前最重要的事其实是：Phase 3 功能（LLM 解释 / SERP / 标注）还没写；
	•	代码更多是“内部工具 + 可能未来商品化”，短期并不需要其他人通过 pip install 来用。

适配度分析

方案 A（标准包结构）

适合：
	•	要作为 可复用库、让别人 pip install keyword-demand-mining；
	•	有意向在 GitHub 上开源，并鼓励别人提 PR；
	•	希望在 CI/CD 里做严格的测试矩阵（Python 3.8–3.12）。

优点：
	•	规范、长期维护成本低；
	•	更利于拆分模块（embedding / clustering / pipeline / evaluation）。

缺点（对你现在）：
	•	重构工作量明显更大（src 目录、包导入、脚本瘦身、CLI 重新设计）；
	•	会挤占你本来要用在 Phase 3 上的时间和精力；
	•	在单人项目阶段，很多“规范收益”用不上。

方案 B（简化结构）

非常符合你现在的情况：
	•	改动集中在：移动文件 + 修路径，风险可控；
	•	想到哪块就进脚本目录直接跑，迭代速度快；
	•	你现在的脚本已经是“按步骤”的形态，放到 core/tools/selectors/lib 结构下，心智模型很简单。

推荐决策

现在这轮重构，建议：

✅ 明确采用「方案 B + 最小标准化增强」

也就是：
	1.	只做 目录整理 + config 路径更新 + 文档分层；
	2.	顶层加 .gitignore、CHANGELOG.md、README.md、.env.example，这已经足够“半标准化”；
	3.	pyproject.toml 目前可选：
	•	如果你准备未来 1–2 周内着手“包化 + CLI 主入口”，可以提前留着；
	•	否则可以先注释掉 [project.scripts]，把它当作“未来草稿”。

方案 A 可以这样规划：
	•	作为「二期重构任务」，时间点放在：
Phase 3 基本功能完成 + 项目总体功能稳定之后。

⸻

4️⃣ 优先级：有哪些更该先做 / 可以延后

如果按“收益 / 风险 / 工作量”综合来看，我会这样重新排序你这 11 个阶段的优先级。

建议的执行顺序（可以映射回你现有阶段）
	1.	阶段 0：备份 + Git 仓库 + 分支
	•	这是硬前提，不动。
	2.	插入一个“基准输出快照”步骤（新）
	•	在动任何结构前，用当前代码再跑一遍：
	•	生成一套「基准 stageA_clusters.csv + cluster_summary_A3.csv + stageB_clusters.csv 等」
	•	把这些文件复制到例如 data/baseline/ 或 tests/fixtures/
	•	这一步会极大增强你后面对比的信心。
	3.	阶段 1：根目录清理 + 文档归档
	•	风险极低，马上提升“视觉清晰度”，对后续操作有心理加成。
	4.	阶段 4：data/ 重组
	•	因为你很多脚本都是围绕 data 的，先把数据位置定死，对后面 config.py 的修改更有锚点。
	5.	阶段 5：config.py 路径统一调整
	•	所有路径只改一处，以后只要脚本都依赖 config，就不会各自乱写路径。
	•	这一步完成后，才开始大规模移动脚本。
	6.	阶段 2：scripts/ 重组 + 导入路径更新（你现在的2+9合并）
	•	这两步最好绑在一起：边移动文件边改 import，避免中间卡在“全红”状态。
	•	并且每完成一个子目录，就跑一下简单测试（比如只跑 A3）。
	7.	阶段 3：docs/ 结构化 + docs/README.md
	•	纯组织性工作，不影响代码，但会让你后面写 Phase 3 文档更舒服。
	8.	阶段 6：.gitignore + .env.example + CHANGELOG.md
	•	这一步收益很高，成本很低，可以放在结构稳定之后做。
	9.	阶段 10：全流程手工回归测试
	•	跑完 A3 → A5 → B3 → HTML → 分析 → validation；
	•	同时对比第 2 步的“基准输出”（哪怕只是人工 spot-check 一些簇的示例短语）。
	10.	阶段 8（README）+ 阶段 11（CHANGELOG 细化）
	•	放在最后写，确保所有变更已经定型。
	11.	阶段 6 中的 pyproject.toml & Makefile
	•	pyproject.toml 可以先只放元数据和 deps，延迟 CLI；
	•	Makefile 属于“锦上添花”，不是第一轮必须。

⸻

5️⃣ 改进建议：最值得加强的 5 个点

这里挑 5 个我认为「改进性价比最高」的点，每条都给“要改什么 / 为什么 / 怎么改”。

⸻

建议 1：在阶段 0 后加一个「基准结果快照」步骤（强烈建议）

要改什么：
	•	在任何结构重构前，固定一个 seed 和参数，跑一次完整流程，把关键输出保存为「baseline」。

为什么：
	•	你这个项目最重要的是「聚类结果的语义稳定性」，不是简单“脚本能跑不报错”；
	•	缺少 baseline，很难知道重构是否“悄悄改变了行为”。

怎么改（示例流程）：
	•	新增一个小脚本 scripts/tools/save_baseline.py，读取当前输出，把统计信息打印出来 & 复制文件到 data/baseline/；
	•	或者手动复制当前输出到 data/baseline/，再写一份 baseline_metrics.md 记录例如：
	•	num_clusters、num_noise_points、某几个典型 cluster 的 top phrases。

⸻

建议 2：把“测试策略”从“纯手动”升级为“最小自动化回归”

要改什么：
	•	在重构的同时，顺手加一点点 pytest，哪怕只测最关键的几个函数。

为什么：
	•	你已经有 cluster_stats.py 和 validation.py，其实非常适合作为 “轻量级自动回归测试” 的基础；
	•	每次重构后只要跑 pytest，就能知道有没有炸得特别离谱。

怎么改（保持简单）：
	•	建一个 tests/ 目录，先写 2–3 个极小的测试，例如：
	•	test_config_paths.py：确认 DATA_DIR / raw... 这些路径存在；
	•	test_clustering_shapes.py：针对一小份 sample 数据，确认输出列齐全、没有 NaN；
	•	test_validation_passes.py：确保 validation.py 在当前数据上通过。

⸻

建议 3：明确「依赖的权威来源」：先只维护 requirements.txt

要改什么：
	•	明确写在文档里：短期内以 requirements.txt 为唯一依赖来源，pyproject.toml 只保存元数据，不作为安装入口。

为什么：
	•	你现在还没真正“包化”，pyproject.toml 和脚本结构其实是错位的；
	•	维护两个来源很容易漂移。

怎么改：
	•	在 README 的「开发环境」里写清楚：
当前项目依赖请以 requirements.txt 为准。
pyproject.toml 仅用于记录项目信息，未来如转为可安装包时再正式启用。
	•	在 pyproject.toml 里暂时去掉 [project.scripts]，等二期包化时再加回来。

⸻

建议 4：在 docs/ 里单独增加一篇「架构与目录设计说明」

要改什么：
	•	现在架构信息分散在重构计划和各个说明里，可以单独写一个：
docs/technical/架构设计.md，专门解释目录设计原则。

为什么：
	•	未来你回头看、或者给别人讲，都需要一篇**“讲清楚为什么这样设计”的文档**；
	•	也方便未来你做「Phase 3 系统化」时，保持一致的结构哲学。

怎么改：
	•	把本次重构计划中的关键部分抽象一下：
	•	为什么有 scripts/core / tools / selectors / lib；
	•	为什么 data 要 raw / processed / results；
	•	将来包化时，src/keyword_mining 会怎么映射这些目录。

⸻

建议 5：把“混合方案”的路线图写清楚，避免未来自己忘记

要改什么：
	•	在 README 或 docs 的某一处写下清晰路线图：
	1.	当前版本：方案 B + 最小标准化（你这次重构完成的结果）；
	2.	下一步（结构相关）：确定什么时候进入方案 A（例如：Phase 3 完成后 / 决定开源后）；
	3.	到方案 A 要做的额外动作：比如建立 src/keyword_mining、把逻辑从 scripts 挪进去、设计 cli.py 等等。

为什么：
	•	你的计划里面已经有“混合方案”的思路，但没有机械性地拆成下一步行动；
	•	半年后再看这个仓库，很容易忘记当时的想法。

怎么改：
	•	在 CHANGELOG.md 或 docs/reference/配置说明.md 附上一个简单小节：
	•	2025-12：完成方案 B 重构，scripts 结构稳定。
	•	计划：当功能稳定 + 有开源需求时，进行二期重构，目标是方案 A 标准包结构。

⸻

🔚 最后给一个「如果现在就要动手」的精简顺序建议

如果你今晚就要重构，我会让你按这个顺序干（都在你现有计划里的内容，只是重排和加两小步）：
	1.	备份 + git 初始化 + 新建 refactor/project-structure 分支（阶段 0）
	2.	跑一遍完整流程，保存一份「baseline 输出」到 data/baseline/（新增步骤）
	3.	清理根目录文档，归档到 docs/history/（阶段 1）
	4.	重组 data/（raw/processed/results），同时更新 config.py 路径（阶段 4 + 5 合并做）
	5.	重组 scripts/ 目录（core/tools/selectors/lib），同步更新导入路径（阶段 2 + 9）
	6.	重组 docs/ 目录并创建 docs/README.md（阶段 3）
	7.	添加 .gitignore、.env.example、CHANGELOG.md（阶段 6 + 11 的一部分）
	8.	跑“全流程回归测试”，同时对比 baseline 的核心指标（阶段 10 + baseline 对比）
	9.	最后再更新 README 里的项目结构与路线图（阶段 8）
