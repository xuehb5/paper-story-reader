# 论证记录与校验器的字段

记录源文本每行格式`<source>-P001-L001<TAB>原文`，PDF用物理页，JATS可将P001视为全文逻辑文本页，并在sources中注明该约定，不能在读者界面称PDF第1页。

顶层：`central_question`；`contribution`含`prior_limit,new_move,bounded_claim`；`entity_states`为`{"object":"对象","states":["状态"]}`数组；`reading_route`为按正文顺序的章节ID数组；`sources`按来源ID建项，每项至少`text_file`（相对本JSON）、`format`、`description`。

`argument_nodes`数组每项含：

- `id,question,claim,test_or_comparison,what_it_does_not_establish,remaining_question`（字符串）。
- `inference_level`是`observation,design_rationale,author_interpretation,model_result,synthesis`之一。
- `story_sections`为本判断所关联的reading_route章节ID数组。
- `evidence`数组，每项`source,page,anchor_start,anchor_end,excerpt`。start/end必须同页、顺序有效、实际存在；excerpt必须是范围内原文的连续摘录。page为整数。

`transitions`按相邻reading_route配对，每项`from,to,resolved,still_unknown,why_next`。`reader_checks`至少两项，每项`question,expected_answer,argument_ids`，后者指向有效论证ID。

```text
python -X utf8 <skill>/scripts/validate_argument_plan.py argument-plan.json --output argument-checks.json
```

校验器只验证字段、目标及摘录存在，不能判定证据支持强度、错误归因或读者是否读懂。对于短问答无需强制建立此记录。
