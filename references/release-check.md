# 来源上下文和正式交付闸门

主交付仍是一份连贯伴读。以下JSON是内部工作材料，不是面向读者的另一份索引，也不能用来宣称自动理解了全部科学语义。

## 工作顺序

1. 在成稿前先读关键来源，记下真实比较组及其条件、分子/片段/样品状态、制备/测量阶段、图中实际对象与指标。结构只差一个基团，不代表实验也只差一个变量。先记录来源事实，再写故事和图解，减少用既成稿件反向找支持的偏差。
2. 把这些事实接成正文和研究图；完成常规`evidence-review.json`。成稿后重新打开来源，不默认初稿或第一张核查表正确。逐项复核所有关键claim，记录实际发现和可见修订。可以独立会话复核时，提供原文、SI、待审稿，避免提供预期答案；没有独立会话如实使用same_agent_second_pass。
3. 完成下面的`context-audit.json`并运行两个检查。被拦截时回源判断，修改具体句子及图谱后同步账本，不仅改哈希或更换证据等级。常见假阳性只在有确切来源时用局部豁免，不能批量豁免。
4. 使用空的新输出目录正式生成，修订选择新的目录保留旧稿与失败。检查真实文字、来源链接和交互，再运行交付校验。最终文件改变必须从数据重生，不能让HTML/MD与账本静默分叉。

```text
python -X utf8 scripts/validate_release.py reader-input.json --review evidence-review.json --init context-audit.pending.json
# init只列待补面板，尚未通过；按真实来源补全后保存context-audit.json
python -X utf8 scripts/validate_evidence.py reader-input.json --review evidence-review.json --output evidence-checks.json
python -X utf8 scripts/validate_release.py reader-input.json --review evidence-review.json --context context-audit.json --output release-checks.json
python -X utf8 scripts/render_reader.py reader-input.json --review evidence-review.json --context-audit context-audit.json --output reader
python -X utf8 scripts/verify_delivery.py reader/PAPER-ID.md reader/PAPER-ID.html --manifest reader/delivery-manifest.json --output delivery-checks.json
```

源码路径按实际Skill位置执行；PAPER-ID替换为真实case.id。语言默认zh，英文伴读在case加`language:"en"`，交付校验传`--language en`。引用PDF文本所需pypdf仍可用实际原页图证据替代；这些闸门本身仅依赖Python标准库。

## context-audit.json

顶层`schema_version:1`；`input_sha256`、`review_sha256`分别绑定当前输入与账本；以下数组不强制固定行数，但需覆盖实际承担推理的关键比较与优势。

- `comparisons`：每项`id`、`pointers`（关联读者可见单元的JSON Pointer）、`groups`（至少两项，各含`label`、`conditions`对象，键为真实条件名称，值为含单位的字符串）、`classification`（`controlled,multi_condition,descriptive`）、`source_claim_ids`。条件名在各组相同，不把浓度、照射时长等变化合并藏入一个“配方”值。超过一个条件键不同，不能标controlled；条件未知不能认证为控制实验。多条件比较需`qualification:{pointer,quote}`，quote逐字出现在当前可见文字中，解释比较限制。不能在正文仍称“唯一差别、只改变、单变量”，只在内部记录承认多变量。若论文确无比较，写至少30字符的`no_comparisons_reason`说明实际研究类型，不编造比较。
- `scopes`：对无需添加物/步骤等阶段性优势、跨对象或跨尺度推论，各含`claim_id`、`stage`、`visible_scope:{pointer,quote}`。限定要在读者相应句子中。整条合成路线、终端交联、样品预处理和测量不能互相代替。
- `panels`：每项`asset`（case.figures键）、`panel`（实际面板或照片身份）、`subject_state`、`metrics`（实际测量指标字符串数组；示意图为空）、`conditions`、`source_locator`、`pointers`（对应可见解释）。每个展示图证需覆盖；一个复合图可多行，尤其不同面板的图例/指标发生变化时单列。只含G′的面板不能讲成G′与G″共同变化；示意、干燥SEM、湿态功能不能串成同一种直接测量。读不清小字先实际放大，仍无法读清则收窄文字并披露，不猜。
- `source_first_review`：`method`为`independent_agent`或`same_agent_second_pass`；`checked_claim_ids`列全部实际复核的规范判断ID；`summary`至少30字符，说明实际回源范围和结果；`findings`数组记真正发现的问题。每项含`id,issue,resolution`（`revised`或`retained_qualified`）、`visible_resolution:{pointer,quote}`、`evidence_claim_ids`。未处理发现项会阻止正式构建。不是每篇都必须发现错误，不能凑数。
- `waivers`可省略。仅对确切来源支持而触发词误报的单元提供`pointer,text_sha256,source_claim_id,source_reason`（至少30字符，具体解释直接证据与适用范围）。它不赋予证据真实性，也不证明语义正确。不能为了通过而把作者推测改标观测，或批量用同一句理由。

JSON Pointer沿用evidence-review.units；图谱标题、finding、图注、侧枝与提要也是可见表述。解释性claim的相关文字应明确作者解释/支持/模型层次，不能单凭NMR峰变化、SEM孔网或宏观模量把特定连接拓扑、湿态结构或全部替代解释写成直接证明。发现原来源自相矛盾时，保留作者报告值和实际不一致位置，给出可证的有限判断，不替作者臆定正确答案。

## 缺材料和Windows中文写入

缺SI时可以只交补料报告并停止，不能伪造完整上下文/审核。此时不运行完整读本生成器，但仍运行`verify_delivery.py companion.md index.html`；有问号替换/中文丢失即失败。Windows上用文件写入工具直接保存UTF-8再运行脚本，禁止把含中文源码经PowerShell here-string管道输给Python。`PYTHONIOENCODING`仅管Python输出，不能补回管道上游已丢的字符。实际读回正文开头、关键条件及补料请求，确认文件可读。


> v0.22扩展：[研究类型路线](study-types.md)与[新证据/材料清单](evidence-blocks.md)补充本契约。旧输入保留原检查；新输入显式选择路线，形式结果记录原文证明状态与假设；DOI可缺省。
