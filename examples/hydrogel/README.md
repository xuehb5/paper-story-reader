# 水凝胶论文：可完整构建的示例

论文：Rui Chen 等，*Photo-regulated disulfide crosslinking: a versatile approach to construct mucus-inspired hydrogels*，Chemical Science 2025，[DOI 10.1039/d4sc08284b](https://doi.org/10.1039/d4sc08284b)。原始论文、SI和图像按 CC BY 3.0 提供；见根目录第三方许可说明。

本示例有7节主线、9项展示图证、4个问题侧枝、阅读脑图和研究论证图。解释光敏接枝、化学响应与宏观成胶的区别、成胶门槛、流变及 BSM 杂化。

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
- `migration.json`：公开示例的路径迁移说明和文件哈希。

核查范围见 `reader-input.json` 的 `coverage`，以及核查记录中的实际方法。本例沿用同一 Agent 的来源优先第二遍记录；开源迁移只改本地路径并重新绑定文件哈希，没有声称新增独立审阅。重建不重新阅读论文，不等于原始实验复现；记录和校验也不保证所有科学语义都正确。
