# 从论文到读本

## 1. 准备材料与 Agent

准备主文及**同一篇论文自己的 SI**，按题名、作者和 DOI 核对配套关系。提供可读文本和清晰原图；扫描文件需要先 OCR，并回看原页确认。不要把检索到的另一篇参考文献误当本篇 SI。

让能够读取文件、查看图像及运行 Python 的 Agent 使用根目录 `SKILL.md`。Skill 本身不含模型、登录凭据或 API 服务。宿主可以是不同的 Agent；是否识别本地 Skill、如何导入，由宿主决定。

用虚拟环境安装 `requirements.txt`。可选页面渲染才需要 `pypdfium2`，普通图像查看可以使用宿主已有工具。

## 2. 建立原文索引

```bash
python scripts/index_source.py article.xml --id paper-main --output work/index
python scripts/index_source.py supporting.pdf --id paper-si --output work/index
```

PDF 使用物理页码；JATS 使用章节、图号和文本锚点，不伪造 PDF 页码。索引辅助定位，不代替实际看图。可选 `--render-pages 2,5` 只用于 PDF，需安装 `pypdfium2`。

## 3. 先写研究故事

先厘清研究问题、对象及状态、设计理由、关键比较、观察、有限结论和下一待解问题。材料论文与化学论文按实际研究选择路线，见 `references/domain-routes.md`。

将科学主线写成能连续读懂的正文，再安排复杂图的局部解释和 SI。必要证据保留在主干；侧枝用于读者可能追问的细节。最后把同一内容结构映射到阅读脑图，单独编写研究论证关系。

## 4. 写入数据与核查记录

按 `references/portable-reader.md` 保存 `reader-input.json`。所有来源和图像路径相对于这个 JSON，避免使用开发者电脑的绝对路径。

```bash
python scripts/validate_evidence.py work/reader-input.json --init work/evidence-review.json
```

初始化只生成待审记录。Agent 必须实际回读原文、查看图像，补齐科学判断、来源摘录/看图记录、可见单元的核查结果；参考 `references/evidence-review-schema.md`。

还需要 `context-audit.json`，记录关键比较的对象/状态/条件、面板指标、结论力度和实际回源修订。格式见 `references/release-check.md`。示例记录只能学习格式，不能冒充新论文的核查。

## 5. 验证并构建

```bash
python scripts/validate_evidence.py work/reader-input.json --review work/evidence-review.json --output work/evidence-checks.json
python scripts/validate_release.py work/reader-input.json --review work/evidence-review.json --context work/context-audit.json --output work/release-checks.json
python scripts/render_reader.py work/reader-input.json --review work/evidence-review.json --context-audit work/context-audit.json --output build/paper-v1
```

缺少已完成核查时，可用 `--draft` 生成明确标注的预览。草稿通过渲染不意味着来源核查完成。

## 6. 阅读与交付

打开生成目录的 `index.html`。读本输出包括论文 HTML、Markdown、图谱文件、本地图像、原始来源及构建/交付清单。

- 点击脑图节点：定位正文；左侧保留当前阅读位置提示。
- 点击左右分叉箭头：镜头移动到同一画布上的侧枝。
- 拖动空白：平移；文字区域仍可选择文字，空格加拖动可从任意区域平移。
- 普通滚轮用于阅读；Ctrl 加滚轮缩放，也可使用缩放控件及“整张纸”。
- 点击图像：查看原图、完整复合图或来源页；点击来源可打开随包原件。

交付前实际检查交互及科学表述，再运行：

```bash
python scripts/verify_delivery.py build/paper-v1/PAPER_ID.html build/paper-v1/PAPER_ID.md --manifest build/paper-v1/delivery-manifest.json
```

将 `PAPER_ID` 换为 `case.id`。示例中是 `A`。后续修改输入或核查结论时，重新回源并生成到新目录，不直接手改最终 HTML。
