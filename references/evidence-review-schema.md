# 内部核查账本

普通读者不需要填写或通读此文件。正文与图谱稳定后先生成待审清单：

```text
python -X utf8 <skill>/scripts/validate_evidence.py reader-input.json --init evidence-review.json
python -X utf8 <skill>/scripts/validate_evidence.py reader-input.json --review evidence-review.json --output evidence-checks.json
python -X utf8 <skill>/scripts/render_reader.py reader-input.json --review evidence-review.json --output reader
```

预览未审内容显式使用`--draft`；仅生成清单不会通过核查。改变输入后需重新核对并更新记录；不得只刷新哈希绕过内容复核。旧稿未迁移账本时仍可草稿预览。

顶层：`schema_version:1`；`input_sha256`绑定完整reader-input文件；`claims`、`units`数组；`reviewer`含`method`（`independent_agent`或`same_agent_second_pass`）、`identity`、`source_first_summary`（实际审阅过程及范围）、`unresolved_items`数组（对象含`issue,disclosure_unit`，指向已准确披露的表述单元）。尚未完成的审阅可另放`pending_checks`数组；非空会阻止正式构建。源本身有未决分歧且已披露，与本轮尚未查看的检查项不同。不能把审核者名或方法字段当作独立身份认证。

`claims`每项：

- `id`唯一；`statement`是保持条件和证据力度的规范判断；`level`取`observation,derived,model_result,author_interpretation,author_claim,background,synthesis`。
- `subject`说明对象/状态；`conditions`说明比较/测量/模型条件；`scope`说明适用区间和例外；`support`说明证据为何支持此判断；`limit`说明更强说法为何不成立，均为非空字符串。
- `evidence`数组。文本证据：`kind:"text",source:"来源ID",locator:"实际段落/图注/表名",quote:"连续原文摘录"`；PDF还需`page`（物理页）。脚本直接从原文件核对摘录，JATS不伪造页码。引用文字过短或公式解析不完整时改用真实图像证据，不编造摘录。
- 图像证据：`kind:"figure",asset:"图证ID",panels:"面板/区域",axes:"坐标/单位，结构图注明无坐标",legend:"样品/图例",conditions:"图的条件",observation:"实际看到什么及例外"`。对应assets必须来自当前sources并通过文件和SHA核验。所有展示图像至少有一条实际看图记录；同一原图重复使用可按相同图像哈希复用。图像记录由实际看图者填写，不能靠图注猜。

`units`由脚本生成JSON Pointer位置和`text_sha256`，覆盖提要、科学标题、主干、侧枝、图解、图注、图谱角色/判断/箭头等。每项补：

- `kind:"factual"`及`claim_ids`，链接支持该单元所有科学判断的记录，可复用多条/同一条；`verdict:"aligned"`或`"qualified"`，`reason`说明与来源比对的结果。仍有误用`needs_revision`，尚未审用`pending`；后二者阻止正式构建。
- 纯阅读动作或无科学断言的导航题，才可`kind:"navigation",claim_ids:[],verdict:"aligned",reason:"为何不含科学主张"`。核查者检查分类，不以题目短就豁免。
- 源内未决矛盾在相应单元准确披露，关联双方证据，记入reviewer.unresolved_items；其`verdict:"qualified"`并说明不做无条件裁决。

研究图`case.research_graph.nodes`各加`claim_id`，`finding`必须与该claim.statement完全相同，title仍单独复核。边的含义/方向/证据类型也在units中审查，不能从节点存在自动推导支持关系。正文可自然改述，但核查单元必须关联相同判断及所需限定；脚本不自动解析其语义一致性。

账本不强制固定论文节点数或证据条数。摘录和看图记录必须足以支撑具体句子，不能只填一个总摘要来形式上覆盖全篇。无需另交“原文索引网页”；读本仍是唯一默认阅读入口，原文/图/来源定位按需提供。
