# 君言英文关键词系统 · Phase 2 聚类优化方案 v1.0

> 站在你的核心需求出发：  
> **对一整批英文短语做需求拆解 → 聚成 60–100 个“语义干净的大类” → 每个大类后面方便继续做维度分类、需求分析。**  
>  
> 这个方案专门解决：  
> - 当前 K-Means 把“完全不相关的东西硬塞在一个类里”的问题  
> - 同时保证：**成本极低（DeepSeek）、流程清晰、后面可以扩展**

---

## 0. 核心思路概括（用人话）

1. **先用算法干净地“聚类”**（不动 LLM，不动 DeepSeek）  
   - 把 12 万多条短语按语义切成 60–150 个“大组”（社区）
   - 原则：**只有真的“互相很像”的短语才会连在一起**

2. **然后对“每个大组”调用一次 DeepSeek，帮你起名字 + 做语义标记**  
   - 每组抽 30–50 条代表短语给 DeepSeek，看它怎么总结
   - 输出：这个组是什么主题、是什么需求方向（工具 / 内容 / 服务…）

3. **最后在每个大组内部继续玩你要的“维度拆解”**  
   - 例如：intent / action / object / channel / audience 等标签
   - 依然尽量靠规则 + 轻量 LLM，而不是对单条短语疯狂砸钱

> 一句话：  
> **“先把短语按‘能不能成为一个微信群’分好组，再让 DeepSeek 给每个群取群名和群介绍。”**

---

## 1. 整体流程总览（流水线视角）

```text
[数据准备 + 向量] 
        ↓
[构建相似度图（谁跟谁很像就拉条边）]
        ↓
[用 Louvain 找“社区”（大聚类）]
        ↓
[聚类后处理：太大拆、太小合、孤立点丢]
        ↓
[每个聚类抽样 30–50 条 → DeepSeek 语义标记]
        ↓
[在标记后的聚类内部做维度标签（intent/action/object…）]
        ↓
[输出：一份人能看得懂、又能继续自动化处理的“需求地图”]


⸻

2. 阶段 A：数据准备与嵌入（你现在其实已经有了）

A.1 输入数据
	•	一批英文短语：phrases（例：125,315 条）
	•	每条有唯一 ID：phrase_id
	•	目前已经用 all-MiniLM-L6-v2 之类的模型算过 embedding（384 维）

A.2 存储建议
	•	表（或文件）形态：

phrase_id | phrase_text                    | embedding (384-d)          | other_meta...
-----------------------------------------------------------------------------------------
1         | "best image compressor online" | [0.12, -0.08, ..., 0.34]   | ...
2         | "free pdf to word converter"   | [0.09,  0.21, ..., 0.41]   | ...
...

	•	这一步你已经在做了，不需要动 LLM，成本为 0。

⸻

3. 阶段 B：主聚类算法 —— 改用“图 + Louvain 社区发现”

B.0 为什么要换思路？
	•	HDBSCAN：需要“密度差异”，但你的向量是“平均摊开”的 → 找不到明显高密度团块 → 直接废掉。
	•	K-Means：强制每条短语必须塞到某个中心 →
导致 “camera + vision board + 餐厅 + 心理学” 乱七八糟混一堆。
	•	你的需求是：
“宁可有一点点噪音，也要一堆特别干净、特别明显的类别。”

图 + Louvain 的核心转变是：

“我不管全局谁跟谁最近，我只管：
‘你周围这 20 个邻居里，有没有特别像的？像就牵条线，不像就别连。’
然后在这个稀疏网络里找“自然形成的朋友圈”。”

⸻

B.1 B1：构建“相似度图”

目标：
把 12 万条短语变成一个图：
	•	每个短语 = 一个节点
	•	如果 语义很像 → 两个节点之间连一条“边”（edge）
	•	边上有“权重”（weight）= 相似度（cosine similarity）

具体操作：
	1.	对每个短语，找 K 个最近邻（K-Nearest Neighbors）
	•	k_neighbors 建议：20–30（初始可以取 20）
	•	距离度量：cosine_similarity（embedding 已经是这个空间）
	•	为了加速，可以：
	•	用 faiss / annoy / hnswlib 做近邻搜索（后面可以交给 Claude 实现）
	2.	设一个“相似度阈值”过滤掉“看起来不太像”的邻居
	•	sim_threshold 初始建议：0.6
	•	对每个点：
	•	只保留 cos_sim >= 0.6 的邻居
	•	用文字表达就是：
“你周围 20 个邻居里，我只保留跟你真的很像的那几位。”
	3.	构建图：
	•	节点：短语 ID
	•	边：(i, j, weight=cos_sim(i,j))
	•	图是稀疏的，大部分点只连 5–20 条边，不是全连。

⸻

B.2 B2：在图上跑 Louvain 社区发现

Louvain 的直观理解：

“如果一群节点之间互相连得特别密，而跟外面连得少，这群就是一个社区。”

操作思路：
	1.	把上一步构建好的图交给 Louvain 算法
	2.	Louvain 会自动：
	•	不需要你设 K 值
	•	自动把图划分成若干个“模块”（社区）
	•	每个社区就是一组短语

关键参数：
	•	resolution：控制社区大小（越大 → 社区越多、越小）
	•	初始可以试 1.0
	•	如果出来的社区太多，可以调低一点 0.8
	•	太少可以调高到 1.2、1.5

⸻

B.3 B3：聚类结果的后处理

Louvain 跑完之后，你会得到：

cluster_id | phrase_id | phrase_text
------------------------------------
0          | 1         | "best image compressor online"
0          | 382       | "image compression tool"
...
1          | 15        | "free pdf to word"
...
999        | ...       | ...

这一步做“形状调整”，让结果贴近你要的“60–100 个大组”。

策略：
	1.	丢弃或合并小得可怜的社区
	•	比如 size < 10 的社区：
	•	要么直接标为“噪音”
	•	要么放入一个统一的 “other_misc” 类
	•	你的需求分析里，这些超级小的类没什么价值，噪音可以接受。
	2.	对特别大的社区再拆一刀
	•	例如：某个社区里有 > 5000 条短语
	•	可能是“大领域”：比如“小说 / 电影 / 娱乐”全混在一起
	•	这时候可在这个社区内部再跑一次 Louvain 或 K-Means：
	•	内部数据量已经很小（比如 5000 条），很好处理
	•	再细分成 3–10 个子社区
	3.	目标形状：
	•	最终留下的社区数（聚类数）大致在 60–150 之间
	•	其中真正参与后续 DeepSeek 语义标记的主力类：60–120 个
	•	一些“small / other类”可以统一并入 few 个“杂项”聚类

⸻

4. 阶段 C：聚类级别的 DeepSeek 语义标记

原则：只对“聚类”调用 LLM，不对“单条短语”逐条调用。
你的成本已经算过：100–1000 个聚类，总成本都在几毛钱人民币到几块钱以内。

C.1 对每个聚类抽样代表短语

对于每个聚类 cluster_k：
	1.	如果这个聚类条目数 ≤ 200：
	•	抽 min(40, 该聚类大小) 条短语作为代表
	2.	如果条目数 > 200：
	•	优先抽：
	•	高频出现的模式（可以按短语长度、常见词排序）
	•	再随机补齐到 40 条

这样做是为了让 DeepSeek 看到“足够有代表性的一锅样本”。

⸻

C.2 设计 DeepSeek 的调用内容（Prompt 思路）

输入给 DeepSeek 的信息（英文或中英文混合都可以）：
	•	你是什么模型：“你是一个关键词需求分析助手”
	•	你要干嘛：
	•	这些短语是同一大类聚类出来的
	•	帮我做三件事：
	1.	总结这个聚类的“主题名称”（英文简短标题）
	2.	用 1–2 句话解释这个聚类的主要“用户需求是什么”
	3.	判断这个聚类偏向于哪类“需求方向”：
	•	tool（找工具 / 软件 / 网站）
	•	content（找内容 / 资料 / 文章 / 视频）
	•	service（找服务 / 人来帮忙）
	•	education/learning（找教程 / 学习路径）
	•	other（其他）
	•	给它那 30–50 条代表短语列表
	•	要求它输出一个结构化 JSON（方便机器读）

输出结构建议：

{
  "cluster_id": 12,
  "cluster_label": "Image compression and optimization tools",
  "cluster_summary": "Users are looking for online tools or apps to compress, resize or optimize images and photos while keeping quality.",
  "primary_demand_type": "tool",
  "secondary_demand_types": ["optimization", "performance"],
  "confidence": 0.92
}

后续你在系统里就保存：
cluster_id = 12 这堆短语 → 就是 “图像压缩优化工具需求”。

⸻

C.3 调用粒度与次数（成本对应的地方）
	•	假设最终参与标记的聚类数是：100 个
	•	每个聚类调用一次 DeepSeek
	•	每次大概 600 输入 token + 100–150 输出 token
→ 成本之前已经算过，大概 0.01–0.02 美金 整体结束。

⸻

5. 阶段 D：在聚类内部做“需求维度拆解”

这一步是给你下一阶段的“需求地图”“标签化系统”铺路。
核心思想：先切“大块”，再在每块里做“维度拆解”。

D.1 建议的维度体系（可以从简单到复杂）

你最终可以给每条短语挂上多个标签，比如：
	•	cluster_id：属于哪一大组
	•	demand_type：工具 / 内容 / 服务 / 学习 / 其他
	•	intent_type：寻找 / 比价 / 教程 / 问题 / 询价…
	•	action：compress / convert / generate / analyze / learn…
	•	object：image / video / pdf / text / website / account…
	•	channel：google / youtube / tiktok / facebook / shopify…
	•	audience：students / developers / marketers / kids …

注意：
	•	demand_type 大部分可以从“聚类级标签”直接继承
	•	比如 cluster 12 是 “image compression tools” → 绝大部分短语都是 tool 类
	•	action / object / channel / audience
→ 更多是在短语内部的分词 + 规则提取就够了，LLM 只是兜底。

⸻

D.2 分词和“主词”的选择原则

针对英文短语：
	1.	用常规 tokenizer 拆成词（word-level），不搞 character 级那一套。
	2.	只关心以下几类词：
	•	动词 / 动作相关：compress, convert, generate, remove, track, monitor…
	•	名词 / 对象相关：image, video, pdf, text, account, website…
	•	渠道名：google, youtube, facebook, instagram, tiktok, shopify…
	•	人群 / 受众：students, kids, developers, designers, marketers…
	3.	对“语法功能词”（the, a, of, in, for, with, to…）直接无视（停用词）。
	4.	不要像中文那样去掉 “best / free / cheap / online”，
因为它们在英文里是非常关键的“意图词”。

所以：“主词”不是从 LLM 中算出来的，而是根据你想要的维度体系，
在人为规则层面定义：哪些词会被特殊关注。

⸻

D.3 如何控制 LLM 的使用量
	•	大部分维度（action / object / channel / audience）可以靠：
	•	你维护一个词表 / 正则规则
	•	甚至连 LLM 都不用，完全纯代码即可
	•	只有在你搞到比较复杂、模糊的短语时，才需要：
	•	小批量丢给 DeepSeek 让它帮你“看一下这是 action 还是 object”
	•	本质上：LLM 是兜底，不是主力。

⸻

6. 阶段 E：质量评估与迭代

E.1 聚类质量的人工验证

对于最终聚成的 60–120 个大类，你可以：
	1.	按“聚类大小”排序，看 Top 20 个大类
	2.	每个大类都抽 20 条短语人工扫一眼：
	•	里面是不是都围绕同一类东西（比如都是“图像压缩工具”）
	•	有没有“明显跑偏”的短语（比如跑进来一个餐厅名）
	3.	如果跑偏太多：
	•	先检查 图构建参数（k_neigh, sim_threshold）是否太松
	•	再考虑是不是 embedding 模型不够好（可以换成更强的）

E.2 指标层面可以看的东西
	•	每个聚类内部的平均相似度（内部越高越好）
	•	聚类之间中心点的相似度（越低越好）
	•	“大聚类”的数量和大小分布：

- 总短语：125,315
- 聚类数：87
- 人均聚类大小：1440
- 最大聚类：5821
- 最小聚类：23
- size<10 的小聚类数量：15 （可以合并/丢弃）

根据这些信息，你可以决定：
	•	是否要调整 Louvain 的 resolution
	•	是否要对某些“大块”再拆

⸻

7. 整体开发顺序建议（给 CloudCoder/Claude Code 看的）

你可以把整个 Phase 2 聚类优化拆成几个具体开发任务：
	1.	Task 1：实现“相似度图构建”模块
	•	输入：phrase_id + embedding
	•	输出：edges 列表（i, j, weight）
	•	参数：k_neighbors、sim_threshold
	2.	Task 2：接入 Louvain 社区发现
	•	用 networkx + python-louvain（or 其他库）
	•	输入：Task 1 的图
	•	输出：每个 phrase_id 的 cluster_id
	3.	Task 3：聚类后处理
	•	小聚类丢弃/合并
	•	大聚类再拆
	•	输出：最终的 cluster_id_clean
	4.	Task 4：DeepSeek 标记聚类
	•	为每个 cluster_id_clean 抽样 30–50 短语
	•	调用 DeepSeek，一次一个聚类
	•	把返回的 cluster_label / cluster_summary / demand_type 存入 DB
	5.	Task 5：在聚类内部做维度标签系统的 Prototype
	•	先实现最简单的两个维度：
	•	demand_type（从聚类继承）
	•	action / object（基于简单词表）

⸻

8. 一句话总结给你
	•	你的核心需求是：
“把一锅乱七八糟的英文短语按真实需求切成 60–100 个大块，每块都尽量‘干净’和‘统一’。”
	•	这套方案的核心转向是：
	1.	不再指望 K-Means 这种“硬塞式”聚类
	2.	换成 图 + Louvain 的“朋友圈”思路
	3.	把 DeepSeek 严格限制在 ‘每个聚类一问’ 的语义标记阶段
	•	成本我已经帮你算过：
按聚类标记，全流程成本忽略不计，真正的工作量在算法实现和标签体系设计上。

你可以直接把这份文档丢给 CloudCoder / Claude，让它按这里的步骤拆成具体开发任务，一块块实现。

