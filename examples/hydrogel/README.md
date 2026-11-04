# 水凝胶论文：可完整构建的示例

论文：Rui Chen 等，*Photo-regulated disulfide crosslinking: a versatile approach to construct mucus-inspired hydrogels*，Chemical Science 2025，[DOI 10.1039/d4sc08284b](https://doi.org/10.1039/d4sc08284b)。原始论文、SI和图像按 CC BY 3.0 提供；见根目录第三方许可说明。

本示例有7节主线、25处展示图证、11个问题侧枝、14处局部读图、5组完整复合图回看，并保留阅读脑图和研究论证图。正文解释研究问题、光敏构件制备、分子变化与宏观成胶、湿态流变、空间控制及 BSM 杂化；侧枝具体讲结构、图例、样品比较和 SI 如何帮助理解这些转折。

在仓库根目录执行：

```bash
python scripts/render_reader.py examples/hydrogel/reader-input.json --review examples/hydrogel/evidence-review.json --context-audit examples/hydrogel/context-audit.json --output build/hydrogel
```

打开 `build/hydrogel/index.html`。来源、图像与核查记录已随包提供，无需联网下载论文或调用模型。

## 文件

- `reader-input.json`：正文、图像、来源和图谱的统一输入。
- `evidence-review.json`：已有的逐单元核查与关键判断证据。
- `context-audit.json`：对象/条件、面板、推断力度和已发现问题的处理。
- `sources/`：原始 JATS 与同篇 SI PDF。
- `figures/`：全文图、SI 原页和用于讲解的局部图像。
- `migration.json`：本次实质阅读设计修订的范围与核查方式。

核查范围见 `reader-input.json` 的 `coverage`，以及核查记录中的实际方法。0.20.1保留原主干科学陈述，新增实质侧枝和局部读图；新增表述、样品身份与图像窗口已经同一Agent回源复读。共211个可见单元、15条规范判断和25处展示图证的面板记录。这不是独立审阅或真人理解测试。

局部图采用SVG视窗显示嵌入的原始位图，不移动图内数据和标注；完整原图/原页仍可回看。Fig.4b的图例靠近c，保留原始b/c同带，分别提示本步看左侧b或右侧c。重建只重放保存的内容，不重新调用模型，不等于原始实验复现。
