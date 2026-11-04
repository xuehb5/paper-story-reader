# 设计参照与适配

记录日期：2026-10-29。以下是公开说明/源码审阅，不是同素材运行排名。本技能独立编写，没有复制第三方渲染代码，也不依赖这些项目已安装。公开可读不自动意味着可直接复制发行。

## 通用阅读与图文呈现

- [xiaofengShi/paper-reading-skill，所读版本](https://github.com/xiaofengShi/paper-reading-skill/blob/61a6333f891c5cb6a8085945fe921bae9094913e/SKILL.md)：参照连续解释、图前具体阅读提示、重要附录就地讲解、内容与来源定位分层。该项目默认交付HTML及Markdown；本作采用材料/化学的两条问题路线来组织内容和流程导航。
- [DeepPaperNote](https://github.com/917Dhj/DeepPaperNote/blob/a0591349dced424dfb45712ad34f9c55122fa9ed/skills/deeppapernote/SKILL.md)：参照写作质量、图表安排与可读性复核；本作不继承其全部笔记归档流程。
- [techdou/paper-reading](https://github.com/techdou/paper-reading/blob/1271fbfbe84c6e69506f2c56c94599f0d6d427da/SKILL.md)：参照按目标控制深度、恢复设计理由与有条件的结论；不把ML术语模板直接搬到材料化学。
- [Mojiajun2022/paper-reading-map](https://github.com/Mojiajun2022/paper-reading-map/blob/ef4537d433d5fdf1fac70e64cf6ca8d821a387ab/SKILL.md)：参照有意义的论证关系、节点与图像/来源关联。本作正文优先，流程图导航到解释段落。

## 已有材料化学适配

- [sanmu-paper-reader](https://github.com/luffysolution-svg/sanmu-skills/blob/main/skills/sanmu-paper-reader/SKILL.md)：已具有材料化学领域文件、同篇正文/SI证据组织及图文对照。此次所读入口Git blob为`1e88167c931d1caccc733984f357710e854108bb`。
- 所读其合成与表征参考的Git blob为`9cd226605f7d161c2cd3618964b72104d71a4c74`，单篇参考为`d555a5f5dce38401657c3f34e01d3f565be2098a`。参照按实际研究选择检查内容、区分样品/状态/测量角色，不继承其全部复现与跨文献功能。
- [Lucaswangzcx/read-paper](https://github.com/Lucaswangzcx/read-paper/blob/main/SKILL.md)也有材料/化学等学科适配条目；此次所读Git blob为`1de269521349f6d77472ca58c9d43719f5a000c8`。

因此，面向材料化学、解释表征、纳入SI、生成流程图均不单独宣称独创。拟验证的设计贡献是把科学问题、连续导读、流程图目标段落与证据位置相互对应，使专业读者更容易理解和定位。

## 科学组织方式的参照边界

- [NIST Materials Structure and Data Group](https://www.nist.gov/mml/mmsd/materials-structure-and-data-group)描述结构与性能关系及多种测量和理论的综合；支持本作围绕结构证据与响应关系编排的领域背景，不意味着本导航结构由NIST验证。
- [ACS Catalysis作者指南](https://researcher-resources.acs.org/publish/author_guidelines?coden=accacs)涉及结构鉴定及正文/SI中的实验资料；仅作材料分布与证据需求的参考，不把期刊投稿规则当作所有论文的阅读要求。
- [IUPAC selectivity](https://goldbook.iupac.org/terms/view/S05563)说明选择性用法依具体语境；本作据此要求保留论文的量定义与比较口径，不用一个通用指标替代所有反应结果。

上述背景不是对每项表征方法的完整专业审定。应用于具体论文时仍以原文、相关原图与SI为依据。
