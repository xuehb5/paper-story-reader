# 用随包生成器稳定生成同纸读本

科学分析由Agent完成；脚本验证来源核查记录与生成数据，不读懂论文、不代写科学判断。先按[来源约束流程](source-fidelity.md)取证、成文并做来源优先第二遍。正文/SI/图已审阅、内容稳定后，写`reader-input.json`与[内部核查账本](evidence-review-schema.md)，运行：

```text
python -X utf8 <skill>/scripts/validate_evidence.py reader-input.json --init evidence-review.json
# 按真实来源审阅补全账本，init不是通过；再运行：
python -X utf8 <skill>/scripts/validate_evidence.py reader-input.json --review evidence-review.json --output evidence-checks.json
python -X utf8 <skill>/scripts/validate_release.py reader-input.json --review evidence-review.json --context context-audit.json --output release-checks.json
python -X utf8 <skill>/scripts/render_reader.py reader-input.json --review evidence-review.json --context-audit context-audit.json --output reader
```

上下文记录见[发布闸门](release-check.md)。生成器直接导出研究论证关系到Markdown、复制本地原件并附链接，写出最终文件哈希清单；不要再手改这些成果。JATS核查及生成依赖Python标准库。PDF文本摘录核查需要当前Python的pypdf；不可用或解析不可靠时用实际PDF页图作为图像证据，不强装。随包`assets/reader`必须保留；不需要Node、模型API、旧项目路径或网络CDN来生成/阅读。PDF取图、浏览器验收另用当前可用工具。旧稿未迁移核查记录时可用`--draft`预览，HTML与文字稿显示草稿状态，构建报告不得写成来源已核实。

## 内容数据契约

顶层是`case`、`assets`、`sources`三对象，可另附`navigation`。路径相对于JSON文件，不写本机固定桌面路径。案例、章节、图证ID限英文字母开头及字母/数字/下划线/连字符。章节标题和数量由论文论证决定。

`case`有字符串`id, short, title, category, paper_title, doi, citation, thesis, audience, coverage`；`source_ids`数组；`sections`数组、`figures`对象和`research_graph`。

- `sections`元素：`id, title, refs`（原文图号/页码/段落锚点字符串数组），`blocks`数组。blocks中的字符串是连续正文；`{"figure":"fig-id"}`是图；`{"figure_row":["id-a","id-b"]}`成对图；`{"detail":{"title":"具体读者问题","kind":"figure-reading","side":"left","paragraphs":["说明"],"figure":"可选图id"}}`是侧枝。多个侧枝图用`figures`数组；SI侧枝kind用`si`，方向也可right。主干必须有实质解释和关键观察。
- `figures`按唯一图证ID建项，每项`label,title,role,caption`。同一原图在两处使用，给两个不同图证ID，可指向同一个image。用原图编号，不制造面板。
- `assets`同ID建项：`source`（sources的键）、`page`（PDF物理页整数，JATS用原始图锚点字符串）、`locator`（实际显示的来源）、`image,page_image,width,height,sha256,page_sha256`。image是局部或完整原图，page_image是完整PDF原页或完整原始图；哈希为对应文件SHA-256。
- `sources`按`<案例id>-main`、`<案例id>-si`建项：`file,sha256,format,description`，PDF另有`pages`。format为pdf或jats。正文JATS时description写DOI和来源，不能编造PDF页码；相关assets加`full_view_label:"查看完整原图",full_view_description:"完整原始图像"`，page_image用该完整原图。PDF可省略这两个标签，默认完整原页。保留正文和SI的真实材料范围，不以“SI已下载”冒充逐页读完。

例如一个图证的引用：

```json
{"source":"T-main","page":"fig-2","locator":"正文 JATS · Fig. 2","image":"inputs/fig2.jpg","page_image":"inputs/fig2.jpg","width":1200,"height":800,"sha256":"实际64位哈希","page_sha256":"实际64位哈希","full_view_label":"查看完整原图","full_view_description":"完整原始图像"}
```

此片段不是可运行案例或科学内容。不能直接保留示意哈希。生成器拒绝未知图/来源、重复章节、图证重复ID、丢图或哈希变化；不负责判断裁剪是否科学合理。输出独立离线HTML、Markdown、共享图谱、资产与构建报告。

## 研究论证图与功能保留

`case.research_graph.nodes`每项为`id,title,role,target,finding,row,column,figure_note,claim_id`。正式构建时claim_id关联账本规范判断，finding与其statement完全相同，避免另造更强的摘要。title是最多18字符的简短问题/判断，仍需语义复核；target必须是实际正文段落ID（如`design-p2`，章节中第2个正文字符串）；role说明其论证用途。row是从0起的布局行，column取left/right/center，同一行可放左右两项或居中一项，不相互重叠。figure_note保留简洁原图号。布局位置不代表证据强度或实验顺序。

`case.research_graph.edges`每项为`from,to,label,kind`，引用真实节点，label明确写“建立样品”“检验分子变化”“提供互补证据”“限定范围”等具体关系；推断/解释可用kind=interpretation画虚线。不要从阅读路线机械连成一串。程序验证目标存在、图形位置和结构，不验证关系在科学上成立。不能建立可靠关系时，用`omit_research_graph_reason`说明原因，界面显示该说明，不凭空造图或默默删掉入口。兼容旧式case.nodes/edges，但新内容优先用research_graph。

若一条边仅提出下一待解问题，label明确写“继续检验……”等，用kind=interpretation区分，不称为支持证据。真正的支持边应说明哪项观察支撑哪项判断；两类边不能混同。

复合图局部的`case.figures[fid].parent`指向完整图ID；完整图在`case.composites[parent]`中给出label/title，同时在assets中提供真实图像、尺寸及哈希。局部和完整图必须同一source/page；page_image仍保留完整原页或原始完整图。没有拆分的完整图无需制造多余“完整复合图”层。

复杂图补读可用`{"walkthrough":{"id":"唯一ID","title":"本步问题","figure":"图ID","lead":"看图任务","paragraphs":["观察与判断"]}}`，放在主干blocks或侧枝detail.blocks中。每个图证使用独立ID；保留面板共同坐标、图例及整体回看，不把面板逐项讲解替换全文主线。

多篇读本可加`navigation:{"home":"../../index.html","papers":[{"id":"T1","short":"水凝胶","href":"../T1/T1.html"}]}`，papers列出实际样品（含当前篇），href/home相对于生成HTML。若仅生成单篇可省略，默认本目录入口。不得为没有生成的论文编造切换链接；集合入口由调用者生成。

另存`argument-plan.json`时，脚本的完整字段要求见[论证记录数据](argument-plan-schema.md)。不凭猜测另建不兼容字段，再把脚本失败当成论文分析失败。

## 来源索引辅助

可先用`scripts/index_source.py <原文.pdf或article.xml> --id T-main --output evidence`生成可追溯文本和来源元数据；对SI另执行一次。PDF索引需要当前Python的pypdf，按需渲染用pypdfium2；工具不可用时使用已有PDF工具，无需强装。JATS走标准库，不补造PDF页码。原图取自可信公开附件或本地文件，Agent仍须实际查看。
