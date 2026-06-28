# JSA 写作基线（Journal of Systems Architecture）

> 从三篇 JSA 2026 论文提炼的写作范式，用于指导本仓库论文（LIR + LVM）的写作与审稿自检。
> 提取的是**语言、结构、论据的组织规律**，不是研究内容。

## 分析样本

- **jsa3**：*Checkpointing and state transfer for industrial controller redundancy*（JSA 178, 2026）
- **jsa**：*InterStellar 2.0: Fine-grained stream–guided HW/SW co-design*（JSA 177, 2026）
- **jsa2**：*LGT4CG: Lightweight GPU-TEE for cloud GPUs*（JSA 178, 2026）

> 逐篇范文的显微镜式解剖（小节结构、时态、语态、高频词汇、图表叙事、语气）见 **jsa_section_writing_attributes.md** 第一部分。两份文件互补：本文件定规则，attributes 定范本证据。

---

## 一、宏观结构基线

**一级标题模式（三篇综合）：**

| 位置 | 常见章节 | 出现率 |
|---|---|---|
| §1 | Introduction | 3/3 |
| §2 | Background | 3/3 |
| §2–3 或末段 | Related Work（位置不固定） | 3/3 |
| §3（可选） | Motivation（独立动机节） | 1/3 |
| 中段 | 方法/设计（名称随论文定制） | 3/3 |
| 中段（安全类专有） | Security Analysis（独立安全论证节） | 1/3 |
| 中段 | Evaluation / Experimental Results | 3/3 |
| 末段 | Discussion（可选） | 1/3 |
| 末段 | Conclusion | 3/3 |

- **Discussion 章节**：非强制。仅 LGT4CG 有单独 Discussion，另两篇将讨论融入各节末尾或 Conclusion。
- **Related Work 位置**：不固定，但当前趋势（3 篇中 2 篇）**后置**至评估之后（§9–10），偏好"先讲清楚自己，再比较他人"。**例外**：jsa3（RSTP）将 Related Work **前置**于 §3（紧接 Background 之后），因为其方法论是"先调研现有方案 → 再定义期望特征 → 再评估 → 最后提出自己的方案"——调研结果直接驱动后续设计，因此前置合理。**判定规则**：如果 Related Work 的调研结论是本文设计的直接输入（如"现有方案都不满足→因此我设计了 X"），前置可行；如果 Related Work 仅作背景铺垫或事后比较，后置更稳妥。
- **Background 节**：三篇均有独立 §2 Background，交代技术背景，不可省略。注意 jsa3 的 §2 Background 较宽泛，包含控制器执行模型、容错概念、容器编排等背景知识，并自然过渡到 §3 Related Work；jsa 和 jsa2 的 §2 Background 更聚焦于技术机制的分类与定义。
- **引言与相关工作**：均独立成节。
- **Motivation 节**（可选）：InterStellar 2.0 在 Background 之后单设 §3 Motivation，用 daxpy 运行示例的量化图（Fig.1/2）证明现有方案的瓶颈，再引出设计目标（Jacobi-2D 的带图详例留到架构节 §4.2.1，§3.4 只文字带过）。适合需要用数据证明"为什么现有方案不够"的论文；若动机已在 Intro 中用数据充分展开可省略。
- **Security Analysis 节**（安全类专有）：LGT4CG 在 Implementation 之后、Evaluation 之前设独立 §Security Analysis，逐类攻击面（固件完整性、BAR攻击、页表攻击、DMA攻击）给出论证，与 Evaluation **完全分开**，不可合并入实验节。
- **节序示例（安全类）**：`Overview → Design → Implementation → Security Analysis → Evaluation → Discussion → Related Work → Conclusion`

---

## 二、引言叙事基线

**建立问题迫切性**——用形容词强化严重性 + 数据/趋势佐证：
> *"The widening gap ... remains a **fundamental limiter** for modern multicore systems."*
> *"public cloud environments introduce a **growing attack surface**."*

**前人局限转折句**——固定句式 `existing/prior work [动词] X, but/however [our gap]`，转折词以 **However / In contrast / While** 为主：
> *"existing solutions are **ill-suited** for controller redundancy ..."*
> *"existing implementations **primarily target** iGPUs. **In contrast**, dGPUs ... have **received little attention**."*

**贡献宣布动词**——倾向强动词 **present / introduce / propose / design / extend**，避免 study、explore 等弱动词。

**贡献标签化**——引言里的"贡献列表"标记方式有两种，均被期刊接受：
- **无编号名词短语 bullet（2/3：jsa、jsa2）**：以名词短语承载成果（"A GPU Shield that…"），不回引，是当前主流；适合贡献彼此交织或与章节非一一对应的论文。
- **`C1–C4` 编号标签（1/3：jsa3）**：后文各节开头回引（"This step addresses C2…"），适合贡献多且章节与贡献有明确对应关系的论文。
> **注意**：`G1/G2/G3`（jsa2）**不是贡献标签**，而是 §3.1 Overview 里的**设计目标**，与引言贡献是两个独立装置（系统/安全类论文常在 Overview 节单列目标，见 §十二）。不要把"目标标签"误当成第三种贡献编号体系。
> **建议**：贡献统一用名词短语承载；若各章节与贡献一对一映射，再叠加 C1–Cn 编号以便交叉引用。

**引言中插图**（可选）——jsa3 在 §1 末尾插入 Fig. 1 展示 5 步工作流，作为结构预告的视觉补充。适合方法论驱动型论文；纯系统类论文通常不在引言中插图。

**结构预告**（强惯例，**非硬规范**）——`"The remainder of this paper is organized as follows. Section 2 reviews ... Section X concludes."`
> 出现率 **2/3**：jsa、jsa3 有；**LGT4CG(jsa2) 没有这一段**，引言在四条贡献 bullet 后直接进入 §2 Background。结论：这是强惯例、保留更稳妥，但**省略不构成不合规**——一篇 JSA 2026 系统/安全论文就省了。投稿前不必因缺这段而判定违规，但建议补上。

---

## 三、方法部分写作基线

- **开头风格**：先给直觉/动机示例（running example）或架构图，再进入形式化定义（方程/EBNF）。
- **模块命名**：功能描述词 + 技术词（GPU Shield, Task Monitor, Nucleus）或首字母缩写（iPP, iBatch, PAQ）。简洁拟功能化，允许隐喻，避免过度拟人。
- **方程与图表引用密度**：高。涉及数值关系处均有编号方程；每个组件配对应图；正文用 `as shown in Fig. X` 强制引用，图表不孤立存在。方程须自含——所有变量在首次出现处定义（如 jsa3 的可调度性/重传预算方程 Eq. 4）。
- **伪代码（Algorithm box）**：当实现逻辑（配置流程、调度判定）用散文难以讲清时，用编号 Algorithm（jsa3 的 Algorithm 1/2 描述 VxWorks 下 TCP/SCTP 配置）。可出现在方法节或评估节，正文须引用并解读，不可只贴代码。
- **大型对比/特征矩阵作为论证工具**：N对象 × M特征的矩阵（jsa3 Table 12：十余种协议 × 多维可靠性/实时/安全特征；jsa2 Table 1：现有 GPU-TEE 调查）用于**论证现有方案的覆盖缺口**，性质上属于方法/动机论证，**不是实验结果表**。判定标准：单元格是"是否具备某特征/属性"而非"实测数值"。另有一类**脆弱性/统计调查表**（jsa2 Table 2：AI 运行时 CVE 统计）同样作动机证据，与特征矩阵并列使用（详见 §十二）。

---

## 四、实验部分写作基线

- **结果呈现**：**全部用散文段落**，不用枚举列表。
- **结果指标**：以正常文字 + 数值嵌入句子，**禁止** `\texttt{metric=value}` 的日志式格式。
- **解读句式**：`As shown in Table/Fig. X, ...`、`We observe that ...`、`Table X demonstrates that ...`、`It is worth noting that ...`。**不用** "Results showed:"、"It can be seen that"。
- **对比 SOTA**：用相对倍数（`up to 2.92×`）和绝对百分比（`average overhead of 4.16%`）；非统计类论文不用 p 值；定性词（significantly）须紧跟数值支撑。
- **结果表格**：不大范围加粗最优值，靠文字解读突出重点。表头：行为对比对象，列为指标维度。
- **多配置鲁棒性评估**：当核心指标受多个外部参数影响时，用参数矩阵覆盖参数空间而非只报告单一最优点（jsa3：13 数据量 × 4 丢包场景；本仓库的 temperature sweep 同属此模式）。先给矩阵结果，再用散文指出趋势与拐点。
- **图表题注**：中等长度自明式，格式 `Fig. N. [简洁描述 + 关键对比维度]`，方法细节放正文而非 caption。

---

## 五、句子级行文基线（决定"原生水平"的核心）

> 这一节是三篇范本与"工程文档式写作"最本质的分水岭。前四节讲"放什么"，这一节讲"怎么连成人话"。

**1. 段落 = 一个论点，不是一份清单。**
每段有一个承载论点的主句，其余句子为它服务（提供机制、数据、例证、推论）。读者读完一段应能用一句话复述该段主张。
- 范本（jsa2 Background）：先立"AI 软件是分层结构"，随后逐层（应用/运行时/驱动）展开，最后落回"高层抽象被翻译为底层执行原语"。整段服务于"分层"这一个论点。
- 反例（清单式）：一段里平行罗列五件并列的事实，无主次，读起来像 bullet 被去掉了符号。

**2. 句间逻辑链：前句结尾的概念，引出后句的开头。**
范本的段落像链条，一环扣一环。这是"读起来像在讲故事"的根本原因。
- 范本（jsa3 引言，概念接力）：
  > 转向网络中心架构 → *这一转变*提升互操作性 → *标准*是互操作的关键 → OPC UA 是关键*标准* → 网络中心架构*使*灵活部署成为可能 → *这*增加了 IT 对 OT 的兴趣 → …… → 需要*冗余* → 冗余需要*状态复制* → 状态复制即 *checkpointing*。
  每一句的尾巴是下一句的头。
- 自检：相邻两句之间能否插入"因此/由此/这意味着/为此"而读起来自然？若每句都是孤立断言、互不衔接，就是清单不是叙事。

**3. 数字嵌进句子，不堆进括号。**
范本把关键数字作为句子的语法成分流出来；只有真正的次要补充才入括号，且一句一般不超过 1 个括号。
- 范本（jsa）：*"improves performance by up to 2.92× and increases memory bandwidth by up to 2.83× over a COTS controller."* —— 数字是谓语的宾语。
- 反模式（本仓库曾出现）：一句话里塞 `(1.8× after zlib)`、`(197.94)`、`(159.99)`、`(Section X)` 四个括号 → 句子被打成碎块。
- 修正：主干数字写进句子（"LIR raw text is 2.6× smaller than JSON, and 13.8× smaller once compiled to bytecode"），仅留一个最必要的交叉引用括号。

**4. 贡献用名词短语承载，避免 "We + 近义动词" 机械排比。**
范本的核心禁忌不是"不用 We"，而是**不用 present/introduce/provide 近义动词三连排比**。三篇范本的贡献列表有两种实际写法：
- **纯名词短语（jsa2 主流）**：*"**A GPU Shield** that secures CPU–dGPU interactions…"*、*"**A Task Monitor** that protects dGPU execution…"* —— 主语是成果本身，无 We。
- **名词短语标题 + We 展开（jsa）**：*"**Revisiting** software-informed memory control. **We** detail the InterStellar HW/SW interface…"*、*"**Finer-grained** expressiveness. **We** generalize the notion of a 'stream'…"* —— 标题是名词/动名词短语，展开句用 We，但动词各不相同（detail / extend / generalize / evaluate），**不是近义动词排比**。
- 反模式：`\textbf{We present} … / \textbf{We introduce} … / \textbf{We provide} …` 三连排比——三个近义动词换着用恰恰暴露"为排比而排比"。
- 修正方向：优先用纯名词短语开头（`\textbf{A bounded-execution VM with capability gating and step-limit guarantees.}`）；若用 We 展开，动词必须多样化且不排比（detail / establish / evaluate 而非 present / introduce / provide）。

**5. 句长有节奏，避免句句等长。**
范本里短断言句（立论点）与长解释句（带机制/条件/数据）交替。通篇等长的中句会读起来像模板填空。

**6. 不在正文替自己的设计/实验辩护。**
范本不写"我们承认 X 会更好，但因为 Y 做不到"。局限与展望集中放在 Discussion / Threats to Validity / Conclusion，且压成陈述句，不在方法或实验正文里反复致歉。

---

## 六、"工程文档惯性"反模式与修正（本仓库实测）

> 这些是本论文（LIR + LVM）实际出现、且与三篇范本明显不一致的写法。逐条按"症状 → 为何不像范本 → 修正"给出。投稿前应清零。

**按严重程度分三级：**
- **硬伤**（审稿人会直接指出）：R1、R2、R5、R8、R9
- **软伤**（影响语感但不违规）：R3、R4、R6、R7

| # | 症状（原文） | 为何不像范本 | 修正方向 |
|---|---|---|---|
| R1 | 贡献列表 `\textbf{We present}/`\textbf{We introduce}/`\textbf{We provide}` 三连 | 范本用名词短语或裸动词，不用第一人称近义动词排比 | 改名词短语加粗开头，成果作主语 |
| R2 | "Evaluation design rationale" 段："We acknowledge that a head-to-head comparison would strengthen…; to our knowledge no prior work… making direct comparison infeasible at this time." | 正文自我辩护/提前认错；范本把这类话留给 Threats to Validity 或不写 | 删整段 rationale，或压成一句移入 §限制讨论 |
| R3 | 正文列代码常量：`single_set, single_read, set_wait_halt, wait_read, set_wait_read, multi_read, pulse` | snake_case 是源码里的 category 字符串，范本正文不出现标识符 | 改自然语言（"单次写、单次读、写后等待…"） |
| R4 | 一句多括号补足（`(1.8× after zlib)`+`(197.94)`+`(159.99)`+`(Section X)`） | 范本数字嵌句，括号稀疏 | 主干数字入句，保留≤1 个交叉引用括号 |
| R5 | "To address these challenges, this paper makes the following contributions:" | 冗余模板前缀（挑战上一段刚讲完） | 直接 "The main contributions are as follows:" 或 "Our contributions are:" |
| R6 | 脚本名 `backend_adapter.py` / `bench_success_at_k.py`、字段 `stage/error_code/message/hint`、配置键 `max_repair_rounds=3`、函数 `compile_to_plan(...)` | 范本提实现只用功能性描述，不精确到文件/字段/键名（仅 Data Availability 节可列文件名指向仓库） | 抽象成"the Python reference implementation""结构化故障信息（阶段、错误码、诊断消息）""at most 3 repair rounds" |
| R7 | 实验结果用枚举 bullet / `metric=value` 日志格式 | 范本结果全用散文，数值嵌句 | 改散文段落 + `As shown in Table X, …` |
| R8 | 摘要/引言中出现 "perfect/zero/every/all/each" 等绝对化修饰词（"blocks **every** unauthorized access"、"**zero** escapes"） | 三篇范本均不使用绝对化修饰词；数字自证，不需要文字帮它喊 | 删掉绝对化修饰词，让数字说话（"blocks unauthorized access requests (UABR = 1.000)"） |
| R9 | 贡献标签含评价性形容词或营销式短语（"**formal** safety analysis"、"**comprehensive** evaluation"） | 范本贡献标签描述具体机制，不含自我评价 | 去掉评价性形容词，改为中性机制描述（"formal safety analysis"→"capability gating and step-limit guarantees"） |

**判定口诀**：正文里凡是"能在你的源码 grep 到的字符串"（文件名、字段名、配置键、category 常量），都应抽象掉，唯一例外是研究对象本身的语言元素（LIR/bytecode 指令 `IOW`/`GTWAY`、设备名 `relay1`、语法 `if/else`）与移植接口（`read_sensor()`）。

---

## 六·二、语气校准基线（决定"读起来像推销还是像研究"的核心）

> 这一节解决三篇范本与"营销式写作"之间最本质的差距。§五–§六讲"不犯语法错误"，本节讲"不犯语气错误"。

### 1. 宣称强度三档分级

| 档位 | 定义 | 典型用词 | 范本态度 |
|---|---|---|---|
| **测量档** | 陈述事实，不加评价 | achieves, yields, reduces, shows, demonstrates, is | 三篇范本默认档 |
| **比较档** | 限定范围的比较 | up to, on average, approximately, in our evaluation, under the tested configuration | 三篇范本常用限定 |
| **推销档** | 带评价性修饰的宣称 | perfect, zero, every, each, remarkable, strong, comprehensive, ensures absolute | **三篇范本从不使用** |

**校准规则**：摘要和引言默认用测量档或比较档，**不用推销档**。实验部分可以用测量档密集报数。

### 2. 绝对化修饰词禁用规则

三篇范本的摘要和引言中，**"every""zero""perfect""each""all"（作强调义）的出现次数为零**。这些词在学术论文中只有一个作用：说服读者。而学术论文的目标是告知读者，让事实自己说话。

| 禁用表达 | 替代方案 | 原因 |
|---|---|---|
| "blocks **every** unauthorized access" | "blocks unauthorized access requests" | "every"是评价，UABR=1.000 是事实 |
| "**zero** escapes" | "no observed escapes" 或直接不写 | "zero"是强调，实验覆盖范围是限定 |
| "**perfect** pass rate" | "pass rate of 1.000" 或 "succeeds on all tasks" | "perfect"是评价，1.000 是数字 |
| "**all** 8,000 adversarial payloads" | "8,000 adversarial payloads" | "all"是多余的强调 |
| "**each** guard contributes independently" | "each guard contributes independently"（这个可以） | "each"在此处是分配义，非强调义 |

**判定口诀**：如果删掉这个词句子意思不变，这个词就是多余的强调——删掉它。

### 3. 贡献列表的内容约束（补充 §十四-4 的形式约束）

§十四-4 解决了"怎么写"（名词短语 vs We+动词），本条解决"写什么"：

- **标签短语中不出现评价性形容词**：~~"A **formal** safety analysis"~~ → "Capability gating and step-limit guarantees"。"formal""novel""comprehensive"都是自我评价，让读者自己判断。
- **量化数字放在展开句中，不在标签中堆砌**：~~"A bounded-execution VM achieving UABR=1.000"~~ → 标签只说机制，展开句再给数字。
- **每条贡献的长度约束**：标签短语 ≤ 15 词；展开句 ≤ 2 句。

### 4. 各节的数字密度控制

| 位置 | 推荐数字量 | 规则 |
|---|---|---|
| 摘要 | 2–3 个关键数字 | 其余用"an order of magnitude""roughly half"等概括 |
| 引言 | 1–2 个（用于建立 gap 的严重性） | 不用于自我评价；贡献列表不堆数字 |
| 方法节 | 按需（公式、参数、阈值） | 数字服务于机制解释，不服务于说服 |
| 实验节 | 密集（正常） | 但每段先一句话概括趋势，再给具体数字 |
| 结论 | 2–3 个（与摘要呼应） | 复述 headline 数字，不引入新数字 |

### 5. 语气对比范例

**推销式（应避免）：**
> The pipeline succeeds on **all** 113 deterministic tasks at temperature=0.0 with a **perfect** pass rate, blocks **every** unauthorized access (UABR = 1.000), and contains **all** 8,000 adversarial payloads with **zero** escapes.

**测量式（范本风格）：**
> The pipeline succeeds on the 113-task deterministic set at temperature=0.0 (pass rate = 1.000). In adversarial fuzzing against 8,000 payloads, the LVM blocks all unauthorized access requests (UABR = 1.000) with no observed escapes under the tested attack classes.

区别：同样的事实，后者没有"every""perfect""zero""all"作强调，数字自己说话，且加了范围限定（"under the tested attack classes"）。

### 6. "This" 开头句子控制（全文 ≤5 次）

"This X introduces/establishes/shows..." 是非母语者最常用的段落首句模式。母语者会交替用："Such a design...", "The result is...", "Consequently,...", "In practice,...", 直接用名词短语开头。

反模式："This vision introduces...", "This compression is...", "This distinction matters...", "This example is developed..." — 连续出现读起来像模板。

操作口诀：写完一段后，检查首句是否以 "This" 开头。如果是，尝试替换为：
- 直接用名词短语开头："The compression ratio reaches..."
- 用因果连接词开头："Consequently,...", "As a result,..."
- 用介词短语开头："In practice,...", "Under this design,..."

### 7. "As shown in" 频率控制（Evaluation 全节 ≤3 次）

"As shown in Table X" 是可接受的引入方式，但连续使用会让 Evaluation 读起来像"数据→数据→数据"的清单。其余引入方式：
- "Table X shows that..."
- 把数字直接嵌入句子主干："Compiling LIR to bytecode yields a 9.8× smaller payload (Table 2)."
- 用因果链引入："Consistent with the payload advantage, the energy measurement (Table 6) confirms..."
- 用主动语态引入："The LVM withstands 8,000 adversarial payloads without observed escapes (Table 7)."

---

## 七、语言与格式基线

- **摘要时态**：描述本文工作用现在时（We present / This work extends / results show）；只陈述已实现结果，**不含括注式免责声明**，限制与展望留给正文。
- **高频固定搭配**：
  1. `In this paper/work, we present/propose/introduce ...`
  2. `To address this [gap/challenge/limitation], we ...`
  3. `As shown in Fig./Table X, ...`
  4. `It is worth noting that ...`
  5. `Experimental/Evaluation results demonstrate/show that ...`
- **人称**：**强烈偏向第一人称 We**（We present / evaluate / implement / observe）。被动语态仅用于客观描述（is allocated, are verified），不用于表达作者行为。
- **引用格式**：数字编号制 `[1]`、`[1–4]`、`[13–18,23]`（Elsevier 标准），按首次出现顺序编号，不用作者-年制。

---

## 八、JSA 写作特征画像（速查）

| 维度 | JSA 基线特征 |
|---|---|
| 结构 | Intro →（Motivation 可选）→ Background → Method →（Security Analysis 安全类专有）→ Eval → Related Work（后置）→ Conclusion |
| 贡献动词 | present / introduce / propose（强动词） |
| 贡献标签 | 纯名词短语 bullet（jsa2，1/3）、名词短语标题+We 展开（jsa，1/3）、C1–Cn 编号（jsa3，1/3）三种均被接受；Gn 是 Overview 的设计目标，非贡献标签 |
| 贡献句式 | 名词短语承载成果（"A GPU Shield that…"），不用 "We+近义动词" 三连排比 |
| 转折句 | "However, existing work X, In contrast, we Y" |
| 段落组织 | 一段一论点，有主句；其余句服务于它，可一句复述全段 |
| 句间衔接 | 概念接力（前句尾→后句头），相邻句间能自然插入"因此/为此" |
| 数字呈现 | 嵌进句子作语法成分；括号稀疏（一句≤1 个），不堆补足括号 |
| 自我辩护 | 正文不替设计/实验致歉；局限集中于 Discussion/Threats |
| 方法展开 | 先直觉示例/动机图，再形式化定义；复杂逻辑用 Algorithm box |
| 论证工具 | 特征矩阵（是否具备）≠ 实验结果表（实测数值） |
| 实验语言 | 现在时为主，散文段落，数值紧跟定性描述；多参数用矩阵覆盖 |
| 标识符 | 正文不出现源码字符串（文件/字段/配置键/category 常量）；仅研究对象的语言元素例外 |
| 人称 | 第一人称 We 主导 |
| 引用 | 数字编号 [N] |
| 题注 | 中长度自明式，含对比维度 |
| 结构预告 | 引言末**多数**有 "organized as follows" 段（2/3；jsa2 省略），强惯例非硬规范 |
| "This" 首句控制 | 全文 ≤5 次以 "This" 开头的句子（§六·二-6） |
| "As shown in" 控制 | Evaluation 全节 ≤3 次（§六·二-7） |
| scope 外项位置 | 仅在 Threat Model 列出，不在 Discussion 重复（§十二-2） |
| 限制排序 | 最可辩护的放第一条，最弱的放最后（§十八·三） |
| 特刊术语对齐 | 用 CFP 的词（edge intelligence, resource-constrained）；闭环机制框定为 intelligence（§十三） |

---

## 九、期刊格式硬规范（来自 Guide for Authors）

> 这些是期刊官方技术要求，不来自样本论文分析，排版/校样阶段会被强制应用。违反任何一条可能导致退回。

### 9.1 文件格式
- **LaTeX 投稿**：提供 `.tex` 源文件 + 所有图片独立文件。PDF **不能**作为源文件提交
- **Word 投稿**：`.doc/.docx`，单栏排版。双栏格式**仅限 LaTeX 投稿**
- 拼写和语法检查必须完成

### 9.2 摘要
- **≤250 词**（硬性上限）
- 必须能独立阅读（常被单独展示）
- 避免引用；如必须引用，给出作者+年份
- 避免非常规缩写；如必须使用，在首次出现时定义
- 现在时陈述已实现结果，**不含括注式免责声明**

### 9.3 关键词
- **1–7 个**关键词，英文
- 避免多词关键词（用 "and" 或 "of" 连接的）
- 仅在领域内已确立的缩写才用于关键词

### 9.4 Highlights（强烈建议提交）
- **3–5 条** bullet points
- 每条 **≤85 字符**（含空格）
- 作为**单独可编辑文件**提交，文件名含 "highlights"

### 9.5 图形摘要（强烈建议提交）
- 尺寸：**531 × 1328 像素**（高×宽），或等比例更大
- 可读尺寸：5 × 13 cm
- 格式：TIFF, EPS, PDF 或 MS Office
- AI 生成图必须符合 Elsevier GenAI 政策

### 9.6 标题
- 简洁且信息丰富
- 尽量避免缩写和公式（除非已广泛理解，如 DNA）

### 9.7 作者信息
- 提供名（given name）和姓（family name），顺序与投稿系统一致
- 机构地址：全称，含国家名
- 标明通讯作者（corresponding author）
- **Author Vitae**：每位作者 ≤100 词，附证件照作为独立图片

### 9.8 方程
- 以可编辑文本提交，**不能截图/嵌图**
- 行内小分数用斜杠 `X/Y`，独立公式用横线
- 变量用*斜体*；指数形式用 `exp(...)` 而非 `e^x`
- 独立方程按正文出现顺序连续编号，附录内单独编号（`Eq. (A.1)` 等）

### 9.9 表格
- 以可编辑文本提交，**不能截图/嵌图**
- 所有表格在正文中有引用，按出现顺序编号
- 说明文字紧邻表格旁，表注放表格正下方
- **禁止**竖线分隔列，**禁止**单元格底纹/阴影
- 谨慎使用表格，确保表格数据不与其他地方描述的结果重复

### 9.10 图版分辨率（投稿时必须满足，否则退回）

| 类型 | 格式 | 最低 DPI | 单栏最小像素宽 | 全页最小像素宽 |
|---|---|---|---|---|
| 矢量图（线图、流程图） | EPS / PDF（嵌入字体） | — | — | — |
| 彩色/灰度照片（半色调） | TIFF/JPG/PNG | 300 dpi | 1063 px | 2244 px |
| 纯位图线图（黑白线条） | TIFF/JPG/PNG | 1000 dpi | 3543 px | 7480 px |
| 组合（位图线条+半色调） | TIFF/JPG/PNG | 500 dpi | 1772 px | 3740 px |

- 矢量图优先（EPS/PDF）；文字相对图像不能过小（防止缩印后不可读）
- 彩色图需对色觉障碍友好（非红绿对立配色）
- 每张图独立文件，命名 `Figure_1.eps` 等；AI 生成图在每张 caption 末及 AI 声明节均需披露
- **禁止**：分辨率过低的文件、文字过小的图片、多图合并为一个文件

### 9.11 单位与术语
- 使用**国际单位制（SI）**；如提及非 SI 单位，需给出 SI 等价物
- 数学符号和术语需前后一致

### 9.12 参考文献
- 数字编号制 `[N]`，按**首次出现顺序**编号
- 正文中可提及作者名，但**必须**给出编号（如 "Barnaby and Jones [8] obtained..."）
- 引用和参考列表**双向一致**（正文中引用的必须在列表中，反之亦然）
- 摘要中引用的参考文献**必须在参考列表中给出完整信息**
- 期刊名缩写遵循 **LTWA（标题词缩写列表）**
- 鼓励提供 DOI 超链接
- 预印本须标注 "preprint" 或服务器名称 + DOI
- 数据集引用在方括号前加 `[dataset]` 标签
- 软件引用需包含：创建者、标题、发布场所、日期、标识符、版本

### 9.13 附录
- 附录用 A, B, C 等标识
- 公式独立编号：`Eq. (A.1)`, `Eq. (B.1)` 等
- 图表独立编号：`Table A.1`, `Fig. A.1` 等

### 9.14 致谢（Acknowledgements）
- 独立节，位于参考列表**之前**
- **不能**放在标题页、标题脚注、或文章其他位置

### 9.15 CRediT 作者贡献声明
- 通讯作者**必须**使用 CRediT 角色声明各作者贡献
- 角色包括：Conceptualization, Data curation, Formal analysis, Funding acquisition, Investigation, Methodology, Project administration, Resources, Software, Supervision, Validation, Visualization, Writing – original draft, Writing – review and editing

### 9.16 竞争利益声明
- **所有作者必须声明**（使用 Elsevier 声明工具）
- 无竞争利益时选择 "I have nothing to declare"
- 声明结果的 Word 文件需上传

### 9.17 资助声明
- 必须披露资助来源及资助号
- 无资助时使用："This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors."

### 9.18 生成式 AI 声明
- **必须声明** AI 工具的使用
- 声明格式："During the preparation of this work the author(s) used [NAME OF TOOL / SERVICE] in order to [REASON]. After using this tool/service, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the published article."
- 基础工具（拼写检查、语法检查）**不需要**声明
- AI 工具**不能**列为作者或共同作者

### 9.19 数据可用性声明
- **Option C**：必须将数据存入相关数据仓库，并在文章中引用和链接
- 如无法共享数据，需说明原因

### 9.20 预印本
- 允许在 SSRN 等预印本服务器分享
- 预印本分享**不影响**编辑流程
- 投稿时可选择在 SSRN 发布预印本

### 9.21 英语
- 使用美式英语**或**英式英语，**不能混用**

### 9.22 会议论文扩展
- 从会议论文扩展的投稿**必须**包含 ≥30% 新材料
- 标题和摘要**必须**与会议论文不同
- 需在投稿信中说明与会议论文的差异

### 9.23 校样修正
- 通讯作者需在 **2 天内**完成校样修正

### 9.24 补充材料
- 与主稿**同时提交**
- 生产团队**不会**检查、格式化或排版补充材料
- 提交后只能在修改阶段添加或替换

### 9.25 评审流程
- **单盲评审**（作者身份对审稿人可见）
- 初始由编辑评估适用性，合适后送 ≥2 位审稿人
- 特刊由客座编辑送审，期刊编辑监督并做最终决定

**参考文献格式细节**
- 期刊名缩写遵循 **LTWA（标题词缩写列表）**
- 鼓励提供 DOI 超链接；数据集参考在方括号前加 `[dataset]` 标签（不进入正式排版）
- 预印本须标注 "preprint" 或服务器名称 + 预印本 DOI；若已正式发表，引正式版

---

## 十、本论文（LIR + LVM）已执行的合规改动

| 问题 | 改动 |
|---|---|
| 缺 Background 节 | 新增 §2 Background（MCU执行模型 / 结构化生成 / 字节码VM与能力安全） |
| Related Work 前置 | 移至 Evaluation 之后（§8） |
| 实验结果用枚举列表 | Exp1/Exp2/Exp4 及 Discussion 改为散文 |
| `\texttt{metric=value}` 日志格式 | 改为散文内联数值 |
| "Results showed:" | 改为 "As shown in Table X, ..." |
| Introduction 自辩段（Positioning） | 删除 |
| §3 Terminology / Key terms 块 | 删除 |
| 摘要括注式免责声明 | 删除，结论化表述 |
| 脚本/字段/配置键源码味引用（R6） | `backend_adapter.py`→"the Python reference implementation"；`stage/error_code/message/hint`→"结构化故障信息（阶段、错误码、诊断消息）"；`max_repair_rounds=3`→"at most 3 repair rounds"；`compile_to_plan(...)`、`task_success_rate=0.970` 均抽象；数据集文件名从正文移除，仅保留于 Data Availability 节 |

> **仍待处理（依据 §五/§六/§六·二，投稿前应清零）**：贡献列表 `We present/introduce/provide` 近义动词三连（R1——若用 We 展开，动词须多样化如 detail/establish/evaluate）；"Evaluation design rationale" 自辩段（R2）；正文残留 category 常量 `single_set` 等七项（R3）；"To address these challenges…" 模板前缀（R5）；摘要/引言中绝对化修饰词 "every/zero/perfect/all"（R8）；贡献标签含评价性形容词（R9——"formal/novel/comprehensive" 应改为中性机制描述，但 "critical gap" 等描述严重性的词可接受）。

---

## 十一、投稿前写作自检清单（按本基线逐项勾选）

> 用途：修改完成后，对照此清单逐条核对；全部通过即视为达到与三篇范本同等的"原生学术写作"水平。分"硬规范"（违反即不合规）与"原生度"（决定读起来是否像人写的）两档。

**A. 结构与规范（硬）**
- [ ] 有独立 §Background；Related Work 后置于 Evaluation 之后
- [ ] 引言末有 "organized as follows" 结构预告段（强惯例；省略不算硬违规，但建议保留）
- [ ] 摘要 ≤250 词、为现在时、只陈述已实现结果、无括注式免责声明（§九.2）
- [ ] 摘要中无非常规缩写；如必须使用，首次出现时定义（§九.2）
- [ ] Keywords 1–7 个，英文，避免多词关键词（§九.3）
- [ ] Highlights 3–5 条，每条 ≤85 字符，单独可编辑文件提交（§九.4）
- [ ] 引用为数字编号制 `[N]`，按首次出现顺序（§九.12）
- [ ] 正文引用与参考列表双向一致（§九.12）
- [ ] 方程/表格为可编辑文本（非截图）；表格无竖线、无底纹（§九.8/9.9）
- [ ] 图满足 DPI 要求与色觉友好（§九.10）
- [ ] 单位使用 SI 制（§九.11）
- [ ] 附录独立编号（A.1, B.1 等）（§九.13）
- [ ] 致谢独立节，位于参考列表之前（§九.14）
- [ ] 文末合规节齐全：CRediT / Competing Interests / Funding / AI 声明 / Data Availability（§九.15–9.19）
- [ ] 英语不混用美式/英式（§九.21）
- [ ] Author Vitae 每位作者 ≤100 词（§九.7）
- [ ] 如从会议论文扩展，含 ≥30% 新材料且标题/摘要不同（§九.22）

**B. 句子级原生度（软，决定成败）**
- [ ] 贡献列表未出现 "We present/introduce/provide" 近义动词三连（R1）；若用 We 展开，动词必须多样化（detail/establish/evaluate，非 present/introduce/provide）
- [ ] 每段可用一句话复述其论点；无"去掉符号的 bullet 清单"式段落（§五-1）
- [ ] 相邻句间有概念接力，能自然插入"因此/为此"（§五-2）
- [ ] 关键数字嵌入句子；任一句括号 ≤1 个，无连续补足括号（§五-3 / R4）
- [ ] 正文无自我辩护/提前认错；局限仅在 Discussion/Threats（§五-6 / R2）
- [ ] 无冗余模板前缀（如 "To address these challenges, this paper makes…"）（R5）
- [ ] 句长有长短节奏，非通篇等长中句（§五-5）

**C. 语气与宣称强度（软，新增 §六·二）**
- [ ] 摘要/引言无绝对化修饰词（every/zero/perfect/all 作强调义）（R8）
- [ ] 贡献标签尽量避免评价性形容词（formal/novel/comprehensive/robust）；"critical gap"等描述严重性的词可接受（R9）
- [ ] 摘要数字 ≤ 3 个，其余用概括性描述
- [ ] 安全分析节句式为"Attackers may attempt X. Mechanism Y. Because Z."，不用 "Our system guarantees/blocks every"
- [ ] 实验段落先一句话概括趋势，再给具体数字
- [ ] "This" 开头句子全文 ≤5 次（§六·二-6）
- [ ] "As shown in" 在 Evaluation 全节 ≤3 次（§六·二-7）
- [ ] side-channel scope 仅在 Threat Model 中列出，不在 Discussion 重复（§十二-2）
- [ ] 限制排序：最可辩护的放第一条，最弱的放最后（§十八·三）
- [ ] readback/retry 框定为 "edge intelligence"（§十三）
- [ ] 不跳到 "carbon footprint" 等无数据支撑的结论（§十三）

**D. 标识符纯净度（软）**
- [ ] 正文 grep 不到源码字符串：无 `.py`/`.sh` 文件名、无 `snake_case` 字段或 category 常量、无 `key=value` 配置键、无 `func(...)` 函数名（R3 / R6 / R7）
- [ ] 例外仅限：研究对象的语言元素（`IOW`/`GTWAY`/`relay1`/`if/else`）与移植接口（`read_sensor()`）
- [ ] 数据集文件名只出现在 Data Availability 节与附录结果表 caption，不在正文叙述

**E. 实验语言（软）**
- [ ] 结果用散文段落，非枚举 bullet
- [ ] 数值紧跟定性描述，无 `metric=value` 日志格式
- [ ] 解读句用 "As shown in Table X, …"，不用 "Results showed:" / "It can be seen that"
- [ ] 定性词（significantly 等）紧跟数值支撑

**F. 安全/系统类结构补全（软，见 §十二）**
- [ ] 有独立的威胁模型与假设（界定可信基线 + 攻击者能力 + scope 外项）
- [ ] （安全/系统类专有）Overview 节交代 Goals → Threat Model → Architecture → Workflow；纯体系结构或通信协议论文可省略 Overview，将目标和威胁模型融入 Background 或 Motivation
- [ ] Security Analysis 节按攻击面逐条论证，与 Evaluation 完全分开
- [ ] 评估节以研究问题（Q1/Q2…）开篇，并单列 Experimental setup 子节
- [ ] 动机证据用特征矩阵 / 脆弱性统计表，而非空泛断言

**G. 特刊定位（软，见 §十三）**
- [ ] 标题/摘要首句同时点出**安全**与**效率**两轴，并出现 "LLM-based edge intelligence" / "resource-constrained edge" 术语
- [ ] 引言把 MCU 显式定位为边缘智能最受限端点，呼应 CFP scope
- [ ] 安全叙事（有界安全执行 / 守卫消融）与效率叙事（紧凑表示 / token 成本 / 能耗）作为两条贯穿主线，非散点数字
- [ ] 不硬蹭隐私（privacy）——本文不涉及，按命中的 scope 项定位即可

**H. 贡献与新颖性（见 §二十三）**
- [ ] 每条贡献双向可追溯（正文有对应章节/实验）
- [ ] 新颖性用具体技术对比说明，非仅用形容词
- [ ] 每个设计决策回答了"为什么不用替代方案 X"

**I. 实验基线充分性（见 §二十三）**
- [ ] 对比基线 ≥ 2 个，含最强已有系统
- [ ] 收益和开销都测了
- [ ] 有参数鲁棒性数据（至少 1 个参数扫描）

**J. 局限性与诚实性（见 §二十三）**
- [ ] 局限主动承认，未来工作与局限对应
- [ ] 报最优+平均，不只报最好

**K. 可复现性（见 §二十三）**
- [ ] 硬件/软件/数据集/超参数完整
- [ ] 代码/数据开源或指出专有依赖

---

## 十二、安全/系统类论文结构补全（基于 jsa2 LGT4CG）

> §一–§八 以三篇综合画像为主，对"系统/安全类论文"特有的开篇结构收得不全。本节专门补 jsa2（安全+系统类）的可复用骨架，对本论文（有界安全执行）直接适用。

**1. Overview 节四件套：Goals → Threat Model → Architecture → Workflow（安全/系统类专有，非所有 JSA 论文必需）。**
jsa2（安全类）§3 在进入具体模块设计（§4）前，先用一个 Overview 节铺四块——这是安全/系统类论文的开篇骨架，纯体系结构论文（如 jsa）或通信协议论文（如 jsa3）不需要：
- **§3.1 Goals**：用 G1/G2/G3 列设计目标（Security / Lightweightness / Compatibility），每条一句话+展开。这是"目标标签"，不是贡献。
- **§3.2 Threat Model and Assumptions**（见下条）。
- **§3.3 Architecture**：一张总架构图 + 两三个核心组件的职责分配。
- **§3.4 Workflow**：编号步骤（❶❷❸…）串起端到端流程，配 Fig.3。
> 本论文映射：可在 Background 之后、Method 之前设 Overview，列 LIR+LVM 的目标（安全有界 / 紧凑 / 可移植）、威胁模型、两层架构图、生成→编译→执行→修复闭环工作流。

**2. 威胁模型与假设（Threat Model & Assumptions）—— 安全论文标配。**
jsa2 §3.2 明确三件事，缺一不可：
- **可信基线（TCB）**：什么被信任（"We trust the GPU microarchitecture…"、"LGT4CG itself is fully trusted"）。
- **攻击者能力**：谁能干什么（"any software outside the TEE, including the OS kernel, GPU driver… may be compromised"）。
- **scope 外项**：明确不防什么（"DoS attacks, side-channel attacks, and physical attacks are outside the scope…, consistent with prior GPU-TEE solutions"）。
> 本论文映射：可信 = LIR 编译器 + LVM 参考实现 + 设备 allow-list；不可信 = LLM 输出（可能越权/越界/格式错误）；攻击面 = 未授权 IOW/IOR、栈越界、坏操作码；scope 外 = 物理篡改固件、侧信道。**先界定这个，Security Analysis 与守卫消融才有锚点。**

**scope 外项的位置规则**：在 Threat Model 中明确列出（"X is outside the scope of this work, consistent with prior [领域] solutions"），在 Discussion 中**不重复**。重复暴露 scope 外项会主动给审稿人递刀子。jsa2 的做法："Denial-of-service (DoS) attacks, side-channel attacks, and physical attacks are also outside the scope of LGT4CG, which is consistent with prior GPU-TEE solutions." — 只在 Threat Model 说一次，Discussion 不再提。

**3. Security Analysis 节：按攻击面逐条"攻击→机制→为何失败"。**
jsa2 §6 不混进实验，独立成节，固定句式：
> *"Attackers may attempt to [攻击动作]. LGT4CG [防御机制]. A tampered image fails this verification."*
逐条覆盖固件完整性、BAR 攻击、页表重定向、DMA 攻击、跨应用攻击、内核二进制篡改、计算图篡改。
> 本论文映射：守卫消融矩阵（no_auth / no_load_validator / no_step_limit / no_call_depth）天然对应"逐攻击面"组织——每个被关掉的守卫=一类攻击面，正文用同款句式论证"开启该守卫时此攻击为何失败"。

**4. 评估节以研究问题开篇 + 独立 Experimental setup。**
- jsa2 §7 开头：*"We answer the following questions: **Q1**: What is the overhead… **Q2**: What is the end-to-end overhead…"* —— 用 Q1/Q2 框住整节，后续小节逐一回答。
- **§7.1 Experimental setup** 单列：平台（Phytium 2000-Plus / RTX 3090）、模型清单、数据集、baseline 定义、迭代次数（"executed for 10 iterations"）、对比配置（Baseline vs LGT4CG）。
> 本论文映射：评估节可用 Q1（紧凑性/token 成本）、Q2（安全守卫有效性）、Q3（闭环修复成功率 SCR）、Q4（能耗/可扩展性）开篇；setup 子节列 MCU 平台、600 任务集、温度扫描配置、各 baseline（JSON / Direct Hex / Arduino C / grammar-constrained）。

**5. 动机证据表：特征矩阵 + 脆弱性统计表两类并用。**
- **特征矩阵**（jsa2 Table 1：现有 GPU-TEE × Type/Protection/TCB/Overhead）论证"现有方案的能力缺口"。
- **脆弱性/统计调查表**（jsa2 Table 2：PyTorch/TF/Python 的 RCE/DoS/MC CVE 计数 + LoC）用真实数据论证"大 TCB = 不安全"这一动机前提。
> 本论文映射：可用一张"现有 LLM→硬件控制表示对比表"（JSON/Hex/C/LIR × 体积/可验证性/安全守卫/可读性）作能力缺口论证；若有 MCU 端故障/越权统计，可作脆弱性证据表。

**6. 脚注用于官方术语对照/澄清。**
jsa2 用脚注做术语映射（"command buffer is referred to as pushbuffer"、"context UUID is referred to as the Runlist ID"），把"官方叫法 vs 本文叫法"挪出正文，保持主干干净。
> 本论文映射：LIR/bytecode 指令与固件实现叫法不一致处，可用脚注对照，避免正文塞实现细节。

---

## 十三、本论文特刊定位（VSI: LLMEI）

> 来源：JSA 特刊 *Security and Efficiency for LLM-Based Edge Intelligence* 官方 CFP（2025-12-02 发布）。这是**投稿定位**约束，决定标题/摘要/引言/相关工作往哪个方向打，与前述"写作风格"正交但同样硬。

**投稿硬信息**
- 投稿系统文章类型**必须选 `VSI: LLMEI`**。
- Final manuscript deadline：**2026-06-30**。
- Guest editors：**Meikang Qiu**（Augusta Univ.，嵌入式/边缘安全背景）、**Wenqi Wei**（Fordham Univ.，ML 隐私/可信 AI 背景）。
- 评审单盲：作者身份对审稿人可见，正文可第一人称引用本团队既往工作，无需匿名化。

**CFP 双轴主题（标题即纲领）：Security AND Efficiency。**
特刊标题与正文反复并置"安全"与"效率"两个词。本论文必须让这两轴在摘要首句就同时显形，不能只讲安全或只讲压缩：
- **安全轴**：有界安全执行、能力门控、守卫消融、LVM 越界/越权拦截 → 命中 "Security / Reliable design / Robust algorithms"。
- **效率轴**：紧凑表示（LIR→bytecode 压缩）、token 成本、片上能耗、资源受限 MCU → 命中 "Energy-efficient computing / Storage and memory / Protocols and architecture"。
> 反模式：摘要通篇讲编译器/字节码细节，不出现 "secure" 与 "edge"，审稿人无法把它归到本特刊。

**术语对齐：用 CFP 的词，把 MCU 定位成"边缘智能最受限端点"。**
CFP 关键词：*LLM-Based Edge Intelligence*、*resource-constrained edge environments*、*on local devices*、*latency / bandwidth*。引言应显式写：LLM 生成可执行物在资源受限 MCU 上直接执行不安全且不经济 → 需要紧凑表示 + 有界安全执行。把 MCU 描述为 edge intelligence 谱系里最极端的一端，而非孤立的嵌入式话题。

**Scope 命中清单（10 项里诚实命中 6 项，不硬蹭）**

| CFP scope 项 | 本论文命中 | 对应证据 |
|---|---|---|
| Security for LLM-based EI | ✓ 强 | 能力门控、守卫消融矩阵、LVM 拦截 |
| Energy-efficient computing | ✓ | 片上能耗测量、字节码体积 |
| Storage and memory system | ✓ | 紧凑表示压缩比（vs JSON/Hex/C） |
| Protocols and architecture | ✓ | 两层 LIR+LVM 架构、生成→执行闭环 |
| Reliable design and framework | ✓ | 闭环修复（SCR）、有界执行保证 |
| New robust algorithms design | ✓ 弱 | 修复反馈循环、温度鲁棒性扫描 |
| Privacy protection | ✗ 不涉及 | —（不要硬加隐私章节） |
| Intelligent resource provision / load balance | ✗ | — |
| Multi-cloud / hybrid cloud | ✗ | —（本文是 on-device，不沾云） |
| Environment impact and evaluation | △ 边缘 | 能耗数据可侧面呼应，但非主线 |

> **定位口诀**：标题/摘要双轴并置（安全+效率）；引言用 CFP 术语把 MCU 拉进 edge intelligence；相关工作朝"LLM 边缘安全"与"资源受限高效推理/执行"两个方向布点；只声明命中的 6 项 scope，privacy/cloud 不碰。Guest editor 背景（嵌入式边缘安全 + 可信 ML）提示：审稿人会重点看**威胁模型是否清晰**与**效率数字是否扎实**——正好对应 §十二的威胁模型补全与既有的压缩/能耗证据。

**闭环机制 = edge intelligence 的核心**：特刊标题包含 "Intelligence"，引言应把 readback/retry 框定为 "adaptive edge intelligence agent"，而非 "a nice feature"。例句："The readback–compare–retry mechanism enables the LLM to observe the device's actual state and repair its program, forming a closed-loop control cycle rather than a fire-and-forget deployment." 这直接呼应特刊标题中的 "Intelligence"。

**Environment impact 的谨慎处理**：能耗数据可侧面呼应，但不要跳到 "carbon footprint"——我们没有碳排放数据。安全写法："The energy reduction in on-device interpretation (Section X) is particularly relevant for battery-constrained edge devices where control-program updates are frequent." 不安全写法："This directly lowers the carbon footprint of frequent control-program updates." 原则：只写有数据支撑的结论，不写推理跳跃。

### 7. 安全类论文的宣称语气规范（补充 §六·二）

安全类论文特别容易写成"我们的系统牢不可破"的语气。以下规则来自 jsa2（LGT4CG）的实际写法：

**Security Analysis 节的句式规范：**
- **标准句式**（来自 jsa2 §6）：`"Attackers may attempt to [攻击动作]. [系统名] [防御机制]. [为何失败]."` —— 先说攻击，再说防御，最后说为什么防住了。**不说** "Our system blocks/prevents/guarantees"。
- **反例**：~~"LGT4CG guarantees that no attacker can..."~~ → 正例："LGT4CG verifies every GPU page table and rejects RAM mappings for sensitive data."

**安全数字的表述规范：**
- UABR=1.000 陈述为事实，不加 "guarantees""ensures absolute" 等修饰
- fuzzing 结果限于 "in our evaluation""under the tested attack classes"，不外推到一般性结论
- 不说 "zero escapes"，说 "no observed escapes under the tested configuration"

**威胁模型假设的表述规范：**
- 假设的措辞用 "We assume"（主动承认），不用 "It is assumed"（被动回避）
- scope 外项明确列出，句式："X is outside the scope of this work, consistent with prior [领域] solutions"（来自 jsa2 §3.2）
- 不在安全分析节替假设辩护（"This assumption is reasonable because..."），辩护放在 Discussion

---

## 十四、语感生成方法（从规则到句子的操作手册）

> §五 说了"不要做什么"，本节说**"怎么写出来"**。这是三篇范本与"按规则润色"之间最本质的差距。

### 1. 概念接力的具体操作方法

§五-2 说"前句结尾引出后句开头"，但没教怎么做到。以下是从三篇范本提取的**四种具体接力模式**，每种附操作步骤和范本实例：

**模式 A：前句宾语 → 后句主语（最常用，约占 60%）**

操作：写完一句后，把它的**宾语或核心名词**拎出来当下一句的主语。

范本（jsa3 Introduction，逐句标注接力词）：
> "Industrial Control Systems (ICS) are undergoing an architectural shift from controller-centric to **network-centric architectures** [1]."
> → "**This transition** aims to improve interoperability and flexibility..."
> → "Standards play a central role in enabling **inter-vendor interoperability**..."
> → "within ICS, **OPC UA** is widely regarded as a key facilitating standard [2]."
> → "**The network-centric architectures** enable flexible controller deployment..."
> → "**Lightweight virtualization technologies**, such as containerization and orchestration, are noted examples..."
> → "**Containerized, hardware-agnostic controllers** further expand deployment options..."

操作口诀：**写完一句，回头看它的宾语，下一句用"这个东西"开头。**

**模式 B：前句结论 → 后句用"但是/然而"推翻或限定（转折接力）**

操作：先承认前句的事实，再用 However/While 引出它的局限。

范本（jsa Introduction，§1 第三段）：
> "Conventional memory controllers attempt to manage throughput and latency using **hardware-only techniques**."
> → "However, **these mechanisms** operate without explicit knowledge of which loop, data structure, or kernel instance generated each access..."
> → "As a result, **commodity controllers** cannot (i) deliberately construct long runs of predictable, row-friendly accesses..."

注意：转折词 However 放在**后句句首**，但后句的**真正主语**是前句的宾语（"these mechanisms" = 前句的 "hardware-only techniques"）。这不是简单的"相关然后转折"，而是"用前句的内容做后句的靶子"。

**模式 C：前句泛化 → 后句具体化（举例或聚焦）**

操作：先说一类事物，下一句用"Specifically"或"for example"聚焦到一个具体实例。

范本（jsa Introduction）：
> "Commodity DRAM subsystems are evolving toward **higher concurrency** rather than fundamentally lower per-access latency."
> → "**Specifically**, DDR5-class dual in-line memory modules (DIMMs) provide multiple semi-independent subchannels per module..."

范本（jsa2 Introduction）：
> "GPU vendors, e.g., NVIDIA, also provide proprietary **GPU-TEE solutions** [24]."
> → "As illustrated in Fig. 1, existing GPU-TEEs can be broadly categorized into **Type-I and Type-II designs**."

操作口诀：如果前句说"有一类东西"，后句就说"其中最典型的是……"。

**模式 D：前句提出问题 → 后句给出方案（问答接力）**

操作：先用一句陈述一个 gap 或 limitation，下一句直接给出解决方案。

范本（jsa Introduction，§1 第五段）：
> "While InterStellar demonstrated that lightweight HW/SW cooperation can substantially improve main-memory efficiency, **two scaling questions** naturally arise..."
> → "(1) **Many-channel** memory systems..."（展开第一个问题）
> → "(2) **Richer stream structures** within complex kernels..."（展开第二个问题）
> → "To address **these questions**, this work presents **InterStellar 2.0**..."

操作口诀：如果前句以"gap/questions/challenges"结尾，后句以"To address this/these"开头。

### 2. 段落"呼吸感"的具体操作方法

§五-5 说"句长有节奏"，但没教怎么控制。以下是从三篇范本提取的**段落内部节奏模板**：

**模板：断言 → 展开 → 例证 → 收束（四步呼吸）**

第一步（断言，1 句，短）：用一句话立论点。读者读完这句就知道这段要说什么。
第二步（展开，2-3 句，长）：解释机制、原因、背景。这是段落的"吸气"。
第三步（例证，1-2 句，中等）：给数据、引用、或具体例子。这是段落的"屏息"。
第四步（收束，1 句，短）：落回论点或过渡到下一段。这是段落的"呼气"。

范本（jsa Introduction，§1 第三段，逐句标注节奏）：

> [断言-短] "Commodity DRAM subsystems are evolving toward higher concurrency rather than fundamentally lower per-access latency." （18 词，立论点）
>
> [展开-长] "Specifically, DDR5-class dual in-line memory modules (DIMMs) provide multiple semi-independent subchannels per module, each with its own command/address interface [10,15]." （28 词，解释机制）
>
> [展开-长] "Server-class platforms and high-performance systems-on-chip (SoCs) further integrate multiple external DRAM channels and interleave physical addresses across channels, often at cache-line granularity, so that consecutive memory lines are striped across channels [9,16]." （40 词，进一步展开）
>
> [收束-短] "This organization increases aggregate delivered bandwidth by allowing multiple memory controllers (MCs) to operate in parallel; however, it also fragments what software perceives as a single logical access stream across channels, so no single controller observes the entire stream." （44 词，落回问题）

注意：虽然最后一句较长，但它用分号分成两半——前半讲好处，后半讲问题，形成**段内转折**。这种"先扬后抑"的收束在三篇范本中非常常见。

**反模式（本仓库常见）：**

> "LIR text is 2.6× smaller than JSON raw text (1.8× after zlib), and 13.8× smaller when cloud-compiled to bytecode. Under system-prompt caching LIR emits 51% fewer output tokens than JSON, although its total token cost exceeds JSON's when the longer system prompt is not cached. The compiler's termination, determinism, and totality are established (Propositions 1--3), with compiler--VM consistency confirmed on 209 verified compiler outputs."

问题：三句话都是中等长度的陈述句，没有断言-展开-收束的节奏。每句都在给新信息，没有一句在"服务"另一句。读起来像 bullet list 去掉了符号。

修正示范：
> [断言] "LIR achieves substantial payload and token savings over JSON." （短，立论点）
> [展开] "Raw LIR text is 2.6× more compact than JSON; after cloud compilation to bytecode, the advantage grows to 13.8×. Under prompt caching, LIR reduces output tokens by 51%." （中，给数据）
> [收束] "These savings stem from a single design choice: replacing self-describing textual keys with positional, varint-encoded instructions." （短，归因）

### 3. 数字嵌句的具体操作方法

§五-3 说"数字嵌进句子"，但没教怎么嵌。三篇范本有三种嵌入模式：

**模式 1：数字作谓语的宾语（最自然）**

范本（jsa 摘要）：
> "InterStellar 2.0 improves performance by **up to 2.92×** and increases memory bandwidth by **up to 2.83×** over a COTS controller."

结构：主语 + 动词 + **数字** + 比较基准。数字是动词的直接宾语。

**模式 2：数字作主语的修饰语**

范本（jsa2 摘要）：
> "The runtime TCB consists of **only about 6K** lines of C code."

结构：主语 + 谓语 + **带数字的宾语**。数字在宾语内部。

**模式 3：数字作独立短句（用于强调转折）**

范本（jsa2 Introduction）：
> "Experimental results show that LGT4CG incurs an average overhead of **4.16%** for DNN inference and **0.34%** for DNN training. For LLMs, the average overhead is **7.10%** on TTFT and **6.05%** on output throughput."

结构：两句并列，每句一个核心数字。不用括号补足。

**反模式与修正：**

反模式：`"LIR text is 2.6× smaller than JSON raw text (1.8× after zlib), and 13.8× smaller when cloud-compiled to bytecode (Section 3.2, Table 2)."`
→ 一句里塞了 4 个数字 + 1 个交叉引用括号。

修正：拆成两句，每句一个核心数字，交叉引用移到句尾或下一句：
> "Raw LIR text is 2.6× more compact than JSON, and the advantage grows to 13.8× after cloud compilation to bytecode (Table 2). Even after zlib compression, LIR maintains a 1.8× advantage."

### 4. 贡献列表的名词短语操作方法

§五-4 说"用名词短语承载"，但没教怎么写。三篇范本的贡献列表有两种具体写法：

**写法 A：名词短语 + that 从句（jsa2 主流）**

> "• **A GPU Shield** that secures CPU–dGPU interactions by establishing a trusted context."
> "• **A Task Monitor** that protects dGPU execution by verifying the correctness of GPU execution primitives against the pre-recorded metadata."

操作：把"We present X that does Y"改成"**X** that does Y"。删掉"We present"，让 X 做主语。

**写法 B：名词短语标题 + We 展开（jsa）**

> "• **Revisiting** software-informed memory control. We detail the InterStellar HW/SW interface..."
> "• **Finer-grained** expressiveness. We generalize the notion of a 'stream'..."
> "• **InterStellar 2.0 for high-bandwidth systems.** We extend this architecture..."
> "• **Extended Experimental analysis.** We evaluate InterStellar 2.0 on..."

操作：用名词短语或动名词（Revisiting/Extending/Generalizing）作 bullet 标题，后跟句号，展开句用 We + **多样化动词**（detail / extend / generalize / evaluate）。关键：展开句的动词必须各不相同，**禁止** present / introduce / provide 近义动词排比。

**内容层面的约束（补充形式约束）：**

形式对了不等于内容对。以下约束确保贡献列表的**内容**也符合范本风格：

1. **标签短语中尽量避免评价性形容词**：
   - 慎用：formal / novel / comprehensive / efficient / robust / strong
   - 这些词多为自我评价；范本让机制本身说话，读者自己判断是否 formal/novel
   - 例外：jsa2 的贡献中用了 "critical gap"——此处 "critical" 描述 gap 的严重性而非自我评价，可接受
   - 反例：~~"A **formal** safety analysis of the 14-instruction set"~~（"formal"是自我评价）
   - 正例："Safety analysis of the 14-instruction set, establishing determinism, progress, and bounded termination"（用事实替代评价）

2. **量化数字放在展开句中，不在标签中堆砌**：
   - 反例：~~"A bounded-execution VM achieving UABR=1.000 on 8,000 payloads"~~
   - 正例：标签说机制（"A bounded-execution VM with capability gating and step limits"），展开句给数字（"achieving UABR = 1.000 in adversarial fuzzing against 8,000 payloads"）

3. **每条贡献的长度约束**：
   - 标签短语：≤ 15 词
   - 展开句：≤ 2 句
   - 超出说明标签不够精炼，需要把细节下沉到展开句

**本仓库修正示范：**

原文（`\textbf{We present} a bounded-execution VM with formal safety analysis`）：
→ 修正 1（写法 A，纯名词短语）：`**A bounded-execution VM** with capability gating and step-limit guarantees for untrusted LLM-generated programs.`
→ 修正 2（写法 B，名词短语标题 + We 展开）：`**Bounded execution with capability gating.** We establish determinism, progress, and bounded termination for the 14-instruction LVM, achieving UABR = 1.000 in adversarial fuzzing against 8,000 payloads.`

注意：两种写法都**不用** "formal safety analysis"——这是评价性形容词（见 §六·二-3），应改为中性机制描述。

---

## 十五、段落叙事结构（从"相关但断裂"到"一环扣一环"）

> §五-2 的"概念接力"只解决了**相邻两句**的连接。本节解决**整段甚至整节**的叙事结构——为什么有些段落读起来像"在推进一个论点"，而另一些读起来像"在罗列事实"。

### 1. 段落的论点链：一句话复述测试的升级版

§五-1 说"每段有一个承载论点的主句，其余句子为它服务"。但这只解决了"有没有主句"的问题。更深的问题是：**主句和支撑句之间的逻辑关系是什么？**

三篇范本的段落逻辑关系只有四种：

| 关系 | 句式 | 范本实例 |
|---|---|---|
| **因果** | A → 因此 B | jsa3: "ICS requires low failure probability → Consequently, fault-tolerance techniques are used" |
| **递进** | A → 而且 B | jsa: "DDR5 provides subchannels → Furthermore, server-class SoCs integrate multiple channels" |
| **转折** | A → 但是 B | jsa2: "Type-I provides comprehensive protection → However, it enlarges the TCB" |
| **例证** | A → 例如 B | jsa: "streaming access patterns appear in complex kernels → e.g., multidimensional stencils" |

**操作方法**：写完一段后，给每句标上逻辑关系词（因此/而且/但是/例如）。如果连续三句都是"而且"（并列），说明这段是清单不是叙事——需要把其中两句改成因果或转折关系。

### 2. 节内叙事弧线：引言的五步推进结构

三篇范本的 Introduction 都遵循同一个**五步推进结构**，只是每步的长度不同：

| 步骤 | 功能 | jsa 实例 | jsa2 实例 | jsa3 实例 |
|---|---|---|---|---|
| **① 问题迫切性** | 用趋势/数据建立"为什么现在重要" | "The widening gap...remains a fundamental limiter" | "public cloud environments introduce a growing attack surface" | "ICS are undergoing an architectural shift" |
| **② 前人方案** | 承认已有工作，不否定 | "InterStellar addressed these limitations by introducing HW/SW co-design" | "researchers have proposed TEEs" | "Standards play a central role; OPC UA is a key standard" |
| **③ 前人局限** | 用 However/While 转折，指出现有方案的 gap | "two scaling questions naturally arise" | "existing Type-II implementations primarily target iGPUs" | "existing solutions are ill-suited for controller redundancy" |
| **④ 本文方案** | 用 To address this 引出自己的方案 | "this work presents InterStellar 2.0" | "we present LGT4CG" | "this work proposes a novel channel-based approach" |
| **⑤ 贡献列表** | 用名词短语 bullet 列出贡献 | 4 bullets | 4 bullets | C1–C4 |

**关键观察**：①→②→③ 是"先扬后抑"（先说有方案，再说不够），③→④ 是"问答"（gap 是问题，本文是答案）。这个节奏在三篇中完全一致。

**本仓库问题**：②→③ 的转折太急——引言第一段就跳到"Existing approaches struggle"，没有先充分展开"前人做了什么"。读者还没理解现有方案的能力，就被告诉"它们不够"。

**修正操作**：在"Existing approaches struggle"之前加一段，展开 2-3 个有代表性的前人方案（Code-as-Policies、RT-2、grammar-constrained decoding），简述它们各自解决了什么问题，然后再用 However 转折说"但它们各自只覆盖了一侧"。

### 3. 方法节的叙事弧线：从直觉到形式化

三篇范本的方法节都遵循"**直觉 → 机制 → 形式化**"的三步推进：

| 步骤 | jsa §4 实例 | jsa2 §4 实例 | 本仓库对应 |
|---|---|---|---|
| **直觉** | Fig.1 的 daxpy 示例 | Fig.2 的架构图 | LIR running example |
| **机制** | §4.1 HW/SW interface 的文字描述 | §4.1 GPU Shield 的状态机描述 | §3 的 EBNF + lowering table |
| **形式化** | §4.3 的 Nucleus 算法 | §4.2 的 Task Monitor 验证规则 | §4 的 operational semantics |

**本仓库问题**：方法节直接从 EBNF 开始，没有"先给一个读者能用手跟着走的例子"。running example 虽然有，但它出现在 EBNF 之后——读者还没理解 LIR 是什么，就看到了语法定义。

**修正操作**：在 EBNF 之前加一段文字描述（不用代码），用自然语言走一遍 running example："Consider a smart agriculture task: the LLM receives 'turn on the water pump and read the water level sensor' and outputs six lines of LIR — first declaring the required devices, then issuing a relay write, a delay, a sensor read, and a halt."然后再给出 EBNF。读者先有直觉，再看形式化。

### 4. 节末收束模式："Conclusions:" + bullet（jsa3 特色）

jsa3 的每个"Step"节（§4/§5/§6/§7）末尾都用一个显式的 **"Conclusions:" + bullet 列表**收束，总结该节的关键发现。这种模式适合**多步方法论驱动型论文**——每步有独立结论，读者可以跳读。

范本（jsa3 §4.3）：
> "Conclusions:
> • Detailed state transfer works targeting ICS redundancy are scarce...
> • Container-based work favors CRIU plus file transfer...
> • We found no comparative evaluation for transferring checkpointed state..."

范本（jsa3 §5.8）：
> "Conclusions:
> • No single protocol satisfies all features.
> • Top candidates: SCTP and OPC UA Client–Server (OPC UA TCP).
> • The real-time feature RT_PT is only partly met..."

**本论文适用场景**：如果论文包含多个独立实验（E1 压缩、E2 安全消融、E4 闭环修复），每个实验节末尾可用"Conclusions:" + bullet 收束，让审稿人快速定位每个实验的核心发现。但注意：这是**可选风格**，非强制——jsa 和 jsa2 都不用这种模式。

---

## 十六、实验节写作实操模板

> §四 说了"结果用散文"，但没给**散文的骨架**。以下是从三篇范本提取的实验节段落模板。

### 实验段落四步模板

每一段实验结果都按这四步写，缺一不可：

**第 1 步：锚定图表（1 句）**
> "As shown in Table X, ..." 或 "Figure Y compares ..."

**第 2 步：给出核心数字（1-2 句）**
> 把最重要的数字嵌进句子，不堆括号。

**第 3 步：解读趋势或原因（1-2 句）**
> "This improvement stems from ..." 或 "The primary source of overhead is ..."

**第 4 步：限定或对比（1 句，可选）**
> "Under non-zero temperatures, this advantage diminishes to ..." 或 "Against Arduino C, the advantage grows to 17.3×."

范本（jsa §9 evaluation 段落）：
> [锚定] "At 32 channels, InterStellar 2.0 improves performance by up to 2.92× [数字嵌句] and increases memory bandwidth by up to 2.83× over a commercial off-the-shelf (COTS) controller." [趋势] "Fine-grained stream tracking alone improves performance by up to 1.35×."

范本（jsa2 §7.2 段落）：
> [锚定] "We observed that the impact of LGT4CG on common OS operations ranges from 0% to 2.357%." [原因] "The overhead primarily arises from the additional Stage-2 address translation performed by the hardware." [限定] "Since most of the OS address space does not rely on dynamic page table permission adjustments for access control, the additional translation introduces only marginal overhead."

**本仓库反模式**：
> "The weighted compression ratio reaches $R_{\text{WEIGHTED}}=4.605\times$ and the average ratio $R_{\text{AVG}}=4.409\times$, while the per-task median ratio is $2.5\times$"

问题：三个数字并列，没有锚定图表，没有解读原因。读起来像日志输出。

修正：
> "As shown in Fig. 6, compact bytecode achieves consistently smaller payloads than JSON across all 113 tasks, with a weighted compression ratio of 4.6×. The median per-task ratio is 2.5×, lower than the mean because a minority of larger tasks compress disproportionately well."

---

## 十七、引言写作实操：逐句拆解范本

> §二 说了引言的宏观结构，但没教**每一句怎么写**。以下逐句拆解 jsa3 的 Introduction 前两段，标注每句的功能和衔接手法。

### jsa3 Introduction 逐句拆解

**第 1 段（问题迫切性 + 背景）：**

| 句号 | 原文 | 功能 | 衔接手法 |
|---|---|---|---|
| 1 | "Industrial Control Systems (ICS) are undergoing an architectural shift from controller-centric to network-centric architectures, in which the network replaces the controller as the system's center [1]." | **立论**：提出趋势 | — |
| 2 | "This transition aims to improve interoperability and flexibility, particularly to support data propagation to AI-driven forecasting and decision-making systems." | **解释**：为什么有这个趋势 | 接力词 "This transition" = 句1的 "architectural shift" |
| 3 | "Standards play a central role in enabling inter-vendor interoperability; within ICS, Open Platform Communications Unified Architecture (OPC UA) is widely regarded as a key facilitating standard [2]." | **聚焦**：从泛化到具体 | 接力词 "inter-vendor interoperability" = 句2的 "interoperability" |

**第 2 段（展开背景 + 引出问题）：**

| 句号 | 原文 | 功能 | 衔接手法 |
|---|---|---|---|
| 4 | "The network-centric architectures enable flexible controller deployment and increase Information Technology (IT) interest in Operational Technology (OT) domains [3–5]." | **递进**：网络化带来更多可能 | 接力词 "The network-centric architectures" = 句1的 "network-centric architectures" |
| 5 | "Lightweight virtualization technologies, such as containerization and orchestration, are noted examples [6–8]." | **例证**：具体化 | 接力词 "Lightweight virtualization technologies" 是句4 "flexible deployment" 的具体形式 |
| 6 | "Containerized, hardware-agnostic controllers further expand deployment options, particularly when not reliant on specialized fieldbuses [5,6]." | **递进**：容器化的好处 | 接力词 "Containerized" = 句5的 "containerization" |

**第 3 段（引出冗余需求）：**

| 句号 | 原文 | 功能 | 衔接手法 |
|---|---|---|---|
| 7 | "ICS provides automation across diverse domains where unplanned downtime is unacceptable and, in some cases, hazardous." | **立新论**：转向可靠性需求 | 话题跳转（从部署灵活性到可靠性），但用"diverse domains"承接前文的广泛适用性 |
| 8 | "Consequently, maintaining a low failure probability is fundamental, motivating the use of fault-tolerance techniques." | **因果**：因此需要容错 | 接力词 "Consequently" + "low failure probability" 是句7 "unacceptable downtime" 的逻辑推论 |
| 9 | "A conventional approach is to use redundancy through the duplication of critical components, such as controllers and network paths, to eliminate single points of failure [9]." | **具体化**：容错的具体方法 | 接力词 "redundancy" = 句8的 "fault-tolerance techniques" |

### 操作口诀

写引言时，每写一句，问自己三个问题：
1. **这句的主语和上句的什么成分有关系？**（如果答不上来，说明两句断裂）
2. **这句在五步推进（迫切性→前人→局限→方案→贡献）中属于哪一步？**（如果连续三句都在同一步，说明该步骤写得太啰嗦）
3. **读者读完这句后，最想知道的下一个信息是什么？**（下一句就给那个信息）

---

## 十八、背景节写作实操

> 三篇范本都有独立 §2 Background。本节拆解其写作模式。

### 背景节的三步模式

**第 1 步：定义核心概念（1-2 段）**
> 用 2-3 句话定义领域核心概念，不引用自己的工作。

范本（jsa3 §2.1）：
> "Industrial controllers are rugged computers designed for longevity in potentially harsh environments. The controller executes the control logic to drive the process to the desired state by reading and writing values to and from field devices that interface with the physical world."

范本（jsa2 §2.1）：
> "AI software has a hierarchical structure, from top to bottom: AI application, the AI runtime, and the GPU driver."

**第 2 步：分类或分层（1 段）**
> 把核心概念分成 2-3 类或 2-3 层，每类/层用 1-2 句话描述。

范本（jsa2 §2.1）：
> "We classify execution primitives into four categories: Malloc, Free, Copy, and Launch."

范本（jsa §2.3）：
> "Two main classes are relevant: Direct streams. Defined by a base address, fixed stride, and iteration count... Indirect streams. Indirect streams compute addresses through one or more levels of indirection..."

**第 3 步：引出本文关注的问题（1 段）**
> 用 "However" 或 "This work addresses" 过渡到本文的切入点。

范本（jsa3 §2，最后一段）：
> "This work addresses challenges related to the fault tolerance of industrial controllers. Hence, this section first introduces ICS and their execution models, then introduces fault-tolerance concepts, and finally, briefly introduces orchestration and containers."

**本仓库对应**：
- 第 1 步：MCU 执行模型（已写）
- 第 2 步：结构化生成方法分类（JSON/Hex/C/grammar-constrained → 缺少这一步的分类对比）
- 第 3 步：引出 LIR 的设计动机（需要一句过渡："However, no existing representation simultaneously satisfies compactness, LLM generation stability, and bounded execution."）

---

## 十八·二、方法论驱动型论文的四步模式（基于 jsa3）

> jsa3（RSTP）代表一种"先调研再设计"的论文类型，其方法论结构与纯系统设计论文（jsa、jsa2）显著不同。本节拆解其可复用骨架，对本论文（LIR + LVM）直接适用——本论文也是先调研现有表示（JSON/Hex/C）、再定义评估维度、再对比、最后提出 LIR。

**四步递进结构：**

| 步骤 | jsa3 对应 | 功能 | 本论文映射 |
|---|---|---|---|
| **① 文献调研** | §4 Checkpointing in literature | 系统检索+覆盖度符号表（●◐○），识别"谁做了什么、做到什么程度" | 现有 LLM→硬件控制表示的调研（JSON/Hex/C/grammar-constrained） |
| **② 特征定义** | §5.2 State-transfer protocol features | 定义期望特征（Rel_RD/RT_PT/Sec_Int 等），用 ID 化命名，按类别分组 | 定义 LIR 的评估维度（紧凑性/可验证性/安全守卫/可读性/token 成本） |
| **③ 实验评估** | §6 Existing protocols—experimental evaluation | 对现有方案按②的维度逐条评估，用实测数据而非空泛断言 | 各 baseline 的压缩比/token 成本/安全性的实测对比 |
| **④ 提出方案** | §7 Proposed state-transfer protocol | 基于③的 gap 提出自己的方案，并在 §7.6 自证满足②的所有特征 | 提出 LIR + LVM，自证满足紧凑性/可验证性/安全守卫 |

**关键写作技巧：**
- **特征命名 ID 化**：jsa3 用 `Rel_RD`、`RT_PT`、`Sec_Int` 等短 ID 命名每个期望特征，后文用 ID 交叉引用，避免反复解释。本论文可借鉴：如 `C_COMP`（紧凑性）、`C_VERI`（可验证性）、`C_SAFE`（安全守卫）。
- **覆盖度矩阵**：jsa3 的 Table 12 是"协议 × 特征"矩阵，单元格为 Fully/Partly/Absent。这种矩阵**不是实验结果表**，而是**论证工具**——论证现有方案的能力缺口。本论文可做"表示 × 评估维度"矩阵（JSON/Hex/C/LIR × 紧凑性/可验证性/安全守卫/可读性）。
- **自证满足**：jsa3 §7.6 逐条回扣 §5.2 的每个期望特征（"RSTP fully fulfills Rel_RD because..."）。本论文应在方法节末尾或评估节开头做同样的自证。

---

## 十八·三、Discussion 节写作指导（基于 jsa2）

> 三篇范本中仅 jsa2 有独立 Discussion 节（§8），但其写法值得参考。Discussion 节的功能是**回应方法/实验节不便展开的"为什么"问题**，不是重复结果。

**jsa2 Discussion 的三类内容：**

1. **设计选型辩护**（§8.1）：为什么选 verification 而非 replay？用"this is because"给出技术理由，不用"we acknowledge"。
2. **假设澄清**（§8.2–8.3）：哪些假设可能被质疑？用"this assumption is reasonable because"给出理由，但**不在方法节辩护**——集中放在 Discussion。
3. **局限与未来工作**（§8.4）：明确列出不支持的能力（"current prototype does not support..."），用陈述句而非致歉句。

**限制的排列顺序**：最可辩护的放第一条，最弱的放最后。
- 第一条：跨平台验证范围（"end-to-end on ESP8266; bytecode confirmed on STM32" — 已做部分，容易辩护）
- 中间：prompt 工程、语法可扩展性（有改进轨迹，可辩护）
- 最后：模型依赖性（"qwen3:8b achieves 0.903" — 最弱，但前面已有缓冲）

**本论文 Discussion 可能包含的内容：**
- 为何选择字节码而非 AST 解释（紧凑性 vs 灵活性的权衡）
- 为何不支持浮点运算（MCU 资源约束 + 安全性考虑）
- LLM 生成质量的温度敏感性——为何选择 temperature sweep 而非固定温度
- 守卫消融矩阵的设计理由——为何选择这四个守卫而非其他
- 可扩展性讨论——指令集扩展到 32 条时的影响

---

## 十八·四、Algorithm box 使用指导（基于 jsa3）

> jsa3 大量使用 Algorithm box（Algorithm 1/2/3），用于描述 TCP/SCTP 拥塞控制和状态传输基准。Algorithm box 适用于**用散文难以讲清的流程逻辑**。

**使用场景判定：**
- ✅ 适合用 Algorithm box：多步骤流程 + 条件分支 + 循环（如编译器的 lowering 流程、LVM 的执行循环、修复闭环的重试逻辑）
- ❌ 不适合用 Algorithm box：纯线性流程（用散文+编号步骤即可）、概念性描述（用架构图即可）

**格式要求（来自 jsa3 范本）：**
- 编号行，每行一个操作或条件
- 变量用斜体，关键字用直立体
- 正文必须引用并解读 Algorithm box（"Algorithm 1 summarizes this behavior"），**不可只贴代码不解读**
- 可出现在方法节或评估节

**本论文候选：**
- 编译器的 `parse_program → compile_program → assemble_ir` 三阶段流程
- LVM 的 `decode → verify → execute` 循环
- 闭环修复的 `generate → eval → feedback → retry` 流程

---

## 十九、全文自查方法论（超越检查清单）

> §十一 的检查清单能帮你"不犯错"，但不能帮你"写得好"。以下三个方法能帮你判断**叙事是否通了**。

### 方法 1：逐段摘要测试

把每一段压缩成一句话（不超过 20 词），然后看这些句子串起来是否构成一个完整的故事。

示范（jsa3 Introduction）：
1. ICS 正在从控制器中心转向网络中心架构。
2. 网络化带来灵活部署和容器化机会。
3. 但 ICS 要求高可靠性，需要冗余。
4. 冗余需要状态复制，即 checkpointing。
5. 现有方案对 checkpointing 的传输机制研究不足。
6. 本文提出一个新的传输协议来填补这个空白。

→ 六句话构成一个完整的故事：趋势 → 机会 → 约束 → 需求 → gap → 方案。

**操作**：写完 Introduction 后，做这个测试。如果六句话串起来像在讲一个故事，说明叙事通了；如果像在列六个不相关的事实，说明需要重新组织。

### 方法 2：删除测试

逐段删除，看文章是否还能读懂。如果删掉某段后文章照样通顺，说明这段是冗余的（可能是在重复前文已经说过的内容）。

### 方法 3：朗读测试

把英文论文大声读出来。如果某句话读到一半需要换气，说明句子太长需要拆。如果连续三句话读起来没有停顿变化，说明节奏太平需要调整。如果读到某句时脑子里在想"这句和上句有什么关系？"，说明衔接断了。

---

## 二十、本基线的使用方法（修订建议）

> 原基线的使用方式是"逐条检查 → 修 bug"。补充后的使用方式应该是"分层递进"，每层配合 §十九 的具体方法论工具：

**第一层：结构合规（§一、§九、§十二、§十八·二）**
→ 先把章节顺序、威胁模型、安全分析节等结构性问题修完。这是硬性的。
→ **工具**：对照 §一 的表格逐章核对；若论文属"方法论驱动型"（先调研再设计），参考 §十八·二 的四步模式。

**第二层：段落叙事（§十五、§十六、§十八）**
→ 按**逐段摘要测试**（§十九 方法 1）检查每段是否有论点、每节是否有叙事弧线。这是决定"读起来是否像在推进一个论点"的关键。
→ **工具**：把每段压缩成一句话（≤20 词），看这些句子串起来是否构成完整故事。

**第三层：句子衔接（§十四-1）**
→ 按四种接力模式（A/B/C/D）检查相邻句子的连接。这是决定"读起来是否像在讲故事"的关键。
→ **工具**：**朗读测试**（§十九 方法 3）——大声读出来，读到某句时脑子里想"这句和上句有什么关系？"说明衔接断了。

**第四层：句子节奏（§十四-2、§十四-3）**
→ 按呼吸感模板调整句长节奏，按嵌入模式调整数字呈现。这是决定"读起来是否舒服"的关键。
→ **工具**：朗读测试——连续三句话读起来没有停顿变化说明节奏太平；读到一半需要换气说明句子太长。

**第五层：标识符纯净度（§六）**
→ 最后扫一遍源码字符串。这是最表层的修 bug。
→ **工具**：**删除测试**（§十九 方法 2）——删掉某段后文章照样通顺说明这段冗余。

原基线的问题是只做了第一层和第五层，跳过了第二到第四层——而这三层恰恰是决定"语感"的核心。

---

## 二十一、Related Work 段落写法（来自 related_work_framework.md）

> 基线 §一 提到 Related Work 后置，但没教**每段怎么写**。以下是从三篇范本提取的段落级写法。

### 单个分类段落的四句式

每个子领域用一段，遵循固定的 4 句逻辑：

| 句 | 功能 | 句式 |
|---|---|---|
| S1 定位句 | 该类做什么 + 代表引用 | "X exploit Y to improve Z [12–18]." |
| S2 展开句 | 典型方法/进展（可选） | "Recent designs extend this idea to..." |
| S3 局限句 | 该类的共同局限（**关键句**） | "However, these approaches assume..." |
| S4 区分句 | 本文与该类的区别 | "In contrast, our work..." |

范本（仿 jsa）：
> *"Stream-aware memory systems exploit access regularity to improve bandwidth utilization [12–18]. Recent designs extend this idea to hardware prefetchers and scratchpad management [19, 20]. **However**, these approaches assume a single memory channel and coarse-grained stream classification. **In contrast**, our work identifies fine-grained sub-streams and coordinates policies across multiple channels."*

### 引用密度规范

| 项目 | 规范 |
|---|---|
| 每个子领域引用数 | 5–10 篇 |
| 区间引用写法 | `[12–18]`（连续）、`[13–18, 23]`（含跳跃） |
| 单篇点名 | 仅对最相关的 1–2 篇直接 point（"X et al. [5] proposed..."），其余打包区间引用 |
| 总引用量 | Related Work 节通常占全文引用的 40%–60% |

### 何时用表格 vs 纯散文

- **用对比表**：存在 ≥3 个直接可比的同类系统，能用统一特征维度逐项对比时
- **用系统检索表**：Related Work 本身是一次系统性文献调查时
- **用纯散文**：先前工作差异是"程度/侧重"而非"有无某特征"时

### 章节过渡句

- **后置时的开头句**："Having presented our results, we now position [系统名] relative to prior work."
- **节末收尾句**（强烈推荐）："The above survey confirms that [具体缺口] remains unaddressed, which is precisely the gap our work fills."

### 本论文建议分类

按技术途径分 3 类：
1. **结构化/受限生成**（grammar-constrained decoding, JSON schema）— 局限：保证语法但不保证语义安全与资源边界
2. **硬件控制的中间表示**（NL 直接控制、直接 HEX 生成）— 局限：要么 token 成本高且不可验证，要么不可读不可生成
3. **MCU 上的安全执行**（字节码 VM、能力安全、有界执行）— 局限：已有 VM 缺少面向 LLM 生成的紧凑表示与闭环修复

收尾句：现有工作要么解决"紧凑可生成"要么解决"安全有界执行"，但未在单一框架内同时满足——这正是 LIR + LVM 填补的缺口。

---

## 二十二、摘要句子级模板（来自 abstract_template.md）

> 基线 §九.2 给了硬性规范（≤250 词、无引用等），但没教**每句怎么写**。以下是从三篇范本提取的 S1–S8 句子序列模板。

### 句子序列（6–9 句）

| 句 | 功能 | 句式 | 范本例句 |
|---|---|---|---|
| **S1** 背景 | 领域定位，暗示重要性 | "[核心资源] is [becoming critical / a fundamental challenge] for [场景]." | jsa: "Memory bandwidth has emerged as a fundamental limiter..." |
| **S2** 问题 | 收窄到具体问题 | "[子问题] remains [unaddressed / a bottleneck], particularly when [限定]." | jsa2: "...existing GPU-TEE implementations primarily target iGPUs..." |
| **S3** 缺口 | 转折词开头，排除先有工作 | "However, existing [approaches] [primarily focus on X / overlook Z]." | jsa3: "However, no systematic comparative evaluation... exists." |
| **S4** 方案 | 强动词宣布本文 | "We present/propose [系统名], [简短定语] [名词] for [目标]." | jsa: "We present InterStellar 2.0, a fine-grained HW/SW co-design..." |
| **S5** 贡献 | 展开 S4，2–3 句 | "[系统名] [动词] [组件] that [解决的问题]." | jsa2: "GPU Shield isolates... Task Monitor verifies..." |
| **S6** 平台 | 评估设置（可省） | "We evaluate [系统名] on [平台], using [benchmark]." | |
| **S7** 结果 | 核心数字，峰值+均值 | "achieves up to X× / on average X× / average overhead of X%" | jsa: "up to 2.92× speedup... average DRAM energy reduction of 24%." |
| **S8** 意义 | 升华（可省） | "These results demonstrate that [结论], making [系统名] practical for [场景]." | |

### 数字规则

- 峰值用 "up to X×"，均值用 "on average"
- 开销用百分比 "average overhead of X%"
- **禁止**只报最好情况
- 关键数字 ≤3 个，其余用概括（"an order of magnitude"、"roughly half"）

### 本论文摘要 S1–S8 对照

- S1：MCU 资源约束场景是否作为领域背景？→ ✅ 已有
- S3：现有方案缺口是否用 However 转折？→ ✅ 已有
- S4："we present LIR + LVM" 是否使用强动词？→ ✅ 已有
- S7：压缩率、安全、可靠性三个核心数字是否都出现？→ ✅ 已有（9.8×、8000 payloads、full pass rate）

---

## 二十三、技术内容自检清单（来自 reviewer_checklist.md）

> 基线 §十一 侧重**写作风格**自检，以下侧重**技术内容**自检——审稿人会从这些角度卡你的论文。

### H. 贡献与新颖性

- [ ] 每条贡献都可以在正文找到对应章节或实验（双向可追溯）
- [ ] 新颖性与已有工作的区别用**具体技术对比**说明，而非仅用形容词（"first"、"novel"需有证据）
- [ ] 每个关键设计决策都回答了"为什么不用替代方案 X"
- [ ] 若声称"首次"，Related Work 节中无反例；若声称"改进"，有数值比较支撑

### I. 实验基线充分性

- [ ] 对比基线 ≥ 2 个，且包含**最强已有系统**（非过时方案）
- [ ] 所有合理的竞争方案都列出，未出现的须在正文解释为何排除
- [ ] 对比条件公平：相同硬件/软件版本/数据集
- [ ] 除了"收益指标"，也测了**开销/代价**
- [ ] 结果中有**参数鲁棒性**数据（至少 1 个参数扫描实验，非单点最优值）

### J. 局限性与诚实性

- [ ] 已知局限在 Discussion 中**主动承认**（而非等审稿人指出）
- [ ] 未来工作方向提及，与局限性对应
- [ ] 数值结果中的"最优情况"和"平均情况"都有报告，不只报最好数字

### K. 可复现性

- [ ] 硬件配置完整（型号、频率、内存容量）
- [ ] 软件环境完整（OS 版本、编译器版本、框架版本）
- [ ] 数据集/benchmark 名称和版本明确
- [ ] 关键超参数（temperature、iteration 数等）在正文或附录中列出
- [ ] 代码/数据开源或指出复现所需的专有依赖

---

## 二十四、反向基线：绝对不能动的内容

> 前面所有章节教"怎么改"，本节教"什么不能改"。修改前逐条检查，任一触及则回滚。

### 结构骨架（不可删减/合并/重排）

| 保护对象 | 具体内容 | 破坏后果 |
|---|---|---|
| 双层架构 10 阶段 | NL→LLM→LIR→Compiler→Verifier→Bytecode→LVM→Hardware I/O→Feedback→Repair Loop | Fig.1 失效，核心创新模糊 |
| 三命题结构 | Proposition 1 (Determinism) → 2 (Progress) → 3 (Bounded Execution) | 逻辑链断裂，安全保证不完整 |
| 评估四问题 | Q1 Efficiency → Q2 Security → Q3 Reliability → Q4 Portability | 实验章节混乱，特刊双轴定位失效 |

### 逻辑链条（不可断）

| 保护对象 | 具体内容 | 破坏后果 |
|---|---|---|
| 安全纵深 4 层 | EBNF Parser (70%) → Static Verifier → LVM Runtime Guards (cap/step/stack/PC) | Defense in Depth 不完整，UABR 保证失效 |
| 压缩对比 4 场景 | Raw LLM (285.9B) → +zlib (150.8B) → Cloud-compiled (10.9B) → vs CBOR | 9.8× claim 失去方法论支撑 |
| 温度→K 递进 | Temperature sweep (0.847) → Grammar-filtered (0.876) → Best-of-K=3 (0.982) | 可靠性策略论证断裂 |
| UABR 两层边界 | Corollary 1: "at the model level"；§7.2: empirical UABR=1.000 | 形式化与实验混淆 |
| 四威胁 actor | malicious LLM / encoding-layer / prompt injection / side-channel | §6 攻击面分析失去锚点 |
| 6+1 攻击面 | Unauthorized / Invalid opcodes / Non-terminating / Malformed / Prompt injection / Side-channel / Physical-safety | §6 与 §7.2 消融实验不对应 |

### 术语与符号（不可混淆）

| 保护对象 | 禁止行为 |
|---|---|
| LIR / Bytecode / LVM 命名 | LIR≠"source code"，Bytecode≠"binary"，LVM≠"interpreter" |
| σ = ⟨p, pc, s, dev, cap, k, L, f, r⟩ | 不删分量，不改符号 |
| 14 指令集 | 不增不减，精确平衡点 |

### 数据精确（不可模糊）

| 数字 | 正确表述 | 禁止 |
|---|---|---|
| 8,000 | "withstands 8,000... with no observed escapes" | 不改 "8,000+" / "thousands" |
| 9.8× | "9.8× smaller payload than optimized JSON" | 不改 "~10×" / "order of magnitude" |
| 2KB | "~2KB RAM"（保留 tilde） | 不删 tilde（estimate 不是 exact） |
| 50-line | "fewer than 50 lines of adapter code" | 不改 "minimal adapter" |
| UABR=1.000 | Corollary: "at the model level"；§7.2: empirical | 不混淆两层 |
| 6→14→7 | 6 lines LIR → 14 bytes bytecode → 7 steps execution | 不改数字或对应关系 |

### 叙事锚点（不可删）

| 保护对象 | 具体内容 |
|---|---|
| 水泵例子 | 6 行 LIR 不可删改，贯穿 Intro→§3.2→Fig.2→§5.5→§7.1 |
| Discussion 四 subsection | Design Trade-offs / Cross-Platform / Closed-Loop / Grammar Scalability，最弱放最后 |
| Related Work 三分类 | 结构化生成 / 中间表示 / MCU 安全执行 + gap 收尾句 |

### 修改前强制检查

1. 是否触及双层架构的任何阶段？
2. 是否删除或重排三命题？
3. 是否合并 Q1-Q4？
4. 是否删减安全机制的任何层次？
5. 是否改变 Table 2 的对比场景？
6. 是否跳过温度扫描的中间步骤？
7. 是否混淆 LIR/Bytecode/LVM 的命名？
8. 是否改动形式化符号 σ 的定义？
9. 是否增减 14 指令集？
10. 是否模糊化关键数字（8,000/9.8×/2KB/50-line）？
11. 是否删除 "at the model level" 限定？
12. 是否替换水泵例子？
13. 是否改变 6→14→7 的对应关系？
14. 是否合并 Discussion 为单一 "Limitations" 节？
15. 是否增删 Threat Model 的四威胁 actor？
16. 是否增删 §6 的攻击面枚举？

**任一答案为"是" → 修改必须回滚或重新论证。**
