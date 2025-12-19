整体上，这个方案是 可以的，而且已经达到了“可落地的 MVP 规格文档”水准，可以直接拿去给 Cloud Code 当执行蓝本。👍

我只建议在几处做一点小修正/补强，让它真正跑起来时更顺手、更少踩坑。

⸻

1. 结论：方向、粒度都对了

你现在这个 v1.0 方案，已经很好地做到几件事：
	•	✅ 架构瘦身到 4 个核心模块（config/core/storage/ai/scripts），符合“先跑通再优雅”的思路；
	•	✅ 三张主表 + cluster_meta 都保留了，而且字段真的做了删减，不是嘴上说 MVP；
	•	✅ Phase 1–4 流程非常清晰，脚本级别都写出来了，Cloud Code 照着实现就行；
	•	✅ UI 坚决不上 Web，改为「导出 CSV/HTML + 人工填写 + 脚本导回」，非常符合你现在的人力结构；
	•	✅ 增量更新、embedding 固定版本、“不删大组只打标记”这些关键策略，也都写死在文档里了。

从“2 周内产出第一批需求卡片”的目标来看：
只要 Cloud Code 不瞎搞，这个方案是能做到的。

⸻

2. 几个我建议你「一定改一下」的小点

都是细节，但不改的话，Cloud 按这份文档实现，很容易出错或卡住。

2.1 Phase 4 导出需求 CSV 时，要把 cluster 信息一起导出

你在「导出需求卡片供审核」那一段里，导出的字段只有：
	•	demand_id / title / description / user_scenario
	•	demand_type / related_phrases_count / business_value / status

但在后面「导入审核结果」的伪逻辑里，又要用到 source_cluster_B 去更新 phrases 的 mapped_demand_id。

也就是说：
	•	CSV 里没有 source_cluster_A / source_cluster_B
	•	导入脚本却想用它们 → 一定报错

建议你在文档里明确写一句类似：

导出 demands_draft.csv 时，必须包含 source_cluster_A 和 source_cluster_B 两列，以便后续导入时能根据 B 组找到对应短语。

这样 Cloud Code 在写 DataFrame 的时候就不会漏掉这两个字段。

⸻

2.2 processed_status 的状态流转，再明确一嘴

你现在的枚举是：
	•	unseen / reviewed / assigned / archived

增量过滤示例里用的是：
	•	未处理：unseen
	•	已关联且需求稳定：直接标记为 archived，不再处理
	•	噪音且频次低：也 archived

建议在文档里加一段小说明（不用写代码），把这四个状态的“生命周期”说清楚，比如：
	•	导入后 = unseen
	•	进入某一轮聚类处理过 = reviewed
	•	已经挂到某个 validated 需求 = assigned
	•	明确判定为无价值/噪音 = archived

这样 Cloud Code 在实现 IncrementalUpdater 时，不会自己乱发明新的状态。

⸻

2.3 tokens 的「简化分类」和 enum 保持一致

现在 tokens 表的 token_type 枚举是：
	•	intent / action / object / attribute / condition / other

Phase 5 简化版里写的是：
	•	暂时只分：intent / action / object / other

这没问题，但你可以加一句说明：

MVP 阶段 LLM 只会输出 intent/action/object/other 四种类型，attribute/condition 先保留在枚举中，后续完整版 Phase 5 再启用。

这样 Cloud 不会试图在第一版里就搞 attribute/condition 的复杂规则。

⸻

2.4 要不要在文档里点名「数据库选型」

你现在的 SQL 示例看起来是偏 MySQL 风格的（AUTO_INCREMENT、ENUM 等）。
Cloud Code 如果默认给你整个 SQLite，ENUM 就会变 tricky。

我建议你在 docs 或开头加一句话指定：
	•	MVP 阶段数据库推荐（选一个你真准备用的）：
	•	要么就说：用 MySQL / MariaDB；
	•	要么就说：用 SQLite，但 ENUM 用字符串字段模拟。

不然 Cloud 可能会“好心”帮你选 SQLite，然后自己瞎定义 ENUM，后面你要上生产时会很难受。

⸻

3. 几个「可以保留但别太执着」的地方

这些不用改文档，只是心里有数：
	1.	不写 tests/ & migrations/：
对现在的你完全 OK。先让 Cloud 把脚本写完、你真正跑了一轮，再考虑加测试和迁移。
	2.	Embedding 缓存版本强校验：
你写了“版本不一致就直接报错让你删缓存”，这个是宁可多一步手工也不搞自动策略。
对你当前阶段完全合理，也能防止 Cloud 自作聪明改模型。
	3.	Day1–Day10 的时间表：
这个更多是你给自己看的，Cloud Code 不会真正理解“Day 3 是哪天”，但它会按阶段顺序来做，已经足够了。

⸻

4. 总体建议：可以作为「MVP v1.0 规范」直接交给 Cloud Code

如果用一句话概括我的意见：

✅ 可以
而且这份文档已经达到了「可直接驱动 Cloud Code 干活」的粒度，
只需要在上面那几处小细节（尤其是 Phase 4 的导出/导入字段）补一句说明，就可以当作 MVP v1.0 冻结版本。

你下一步可以这样用它：
	1.	把这份文档当成单独的 docs/mvp_spec_v1.0.md；
	2.	给 Cloud Code 的指令里，明确让它：
	•	先根据这份文档创建目录结构 + models + repository；
	•	再按 Phase 1→2→3→4 的顺序实现对应脚本；
	3.	真正跑完第一轮，从 5万词里产出 10–20 个 validated 需求之后，再开一个 v1.1 文档做调整。

