# 跨学科证据块与材料清单

通用生成器仍保留原图、复合图与逐步读图。正文和`detail.blocks`新增`table`、`equation`、`quotation`块。完整字段示例见[英文数据契约](en/evidence-blocks.md)，下述要求同时适用于两种语言。

每个块均需唯一安全`id`、原始`label`、解释性`title`、真实`source`和`locator`。PDF使用1起算物理`page`，其他格式不能编造PDF页码。引用本地哈希核实的来源。表格每个表头/单元格、公式表达式/变量解释、引文及解释都进入正文可见内容的核查账本。

- 表格：`columns`为字符串列表，`rows`为矩形字符串二维数组，`caption`保留数据集、划分、条件、单位、误差与选择范围。摘取部分行要标明；不得无声组合不同任务。可同时用原图块保留原表视觉证据。
- 公式：`expression`提供可读表达式；`variables`逐项提供`symbol`和`meaning`；`explanation`把式子接回当前问题。可选`mathml`只支持白名单展示标签，不允许脚本、外链、样式或声明。浏览器离线呈现后对照原式检查。公式显示正确不等于推导正确。
- 引文：`text`是简短的原文连续摘录，必须与同来源、同页的已核实文本证据记录一致；`explanation`说明它的论证作用。遵守原始材料许可，不用大段摘录代替解释。

证据索引会列出这些块并定位到同一画布上，包括左右侧枝。论证图新增明确关系：`support`、`comparison`、`interpretation`、`deduction`、`assumption`、`contradiction`、`association`、`next_question`、`limitation`；保留旧`evidence`兼容。标签和方向应表达真实关系，不能把阅读先后画成因果。

`case.doi`可缺省。`case.source_url`应为真实HTTPS来源；缺省时链接本地论文原件。不得伪造DOI。

可用`case.materials`记录附件：`id`、`role`（`main`、`supplement`、`appendix`、`extended_data`、`code`、`data`、`other`）、`status`（`available`、`not_provided`、`not_published`、`not_applicable`）和真实`note`。`available`必须有对应本地来源ID；`not_published`/`not_applicable`必须有原文或官方页面依据`basis`。远程代码网址不是已获取本地代码。可用性和已读范围不同，仍须在正文/覆盖说明中交代实际阅读。

新增来源格式`text`（UTF-8，保留明确定位）和`image`（独立原始补充图，仅接受实际视觉证据）。原PDF、JATS不变。保留下载原件；不能把网站二手摘要标成论文原文。
