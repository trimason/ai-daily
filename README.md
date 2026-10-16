# AI 前沿日报

面向中文阅读的大模型与具身智能研究日报网站。每期保留独立链接，提供历史归档和 RSS，适合在电脑和手机上阅读。

网站：<https://trimason.github.io/ai-daily/>。源码仓库：<https://github.com/trimason/ai-daily>。

当前首页为2026年10月16日日报：围绕编码Agent怎样调度和改进机器人技能、长程Agent怎样处理上下文与成本、世界模型怎样验证动作后果三个问题，交叉阅读AdaRSI、Step 5、Meta Muse与WorldOracle等新材料；同时跟进国内模型架构、开放权重和机器人数据生成。本期RSI成本分析是具体研究的对照阅读，Gemini 4保留为有原日期的历史动向，均不设固定推荐位。每日技术点讲GQA与KV cache，区分缓存容量、推理速度与长上下文能力。选题随新增研究和实际讨论证据轮换；新研究不自动标为社区热点。此前四期保留在归档。

## 本地构建与预览

构建只使用 Python 标准库，无需安装第三方依赖。在本项目目录运行：

```sh
cd ai-daily
python3 scripts/build.py --base-path /ai-daily --site-url https://trimason.github.io/ai-daily
```

生成的静态文件位于 `dist/`，无需提交这些文件。GitHub 部署工作流会重新构建。

本地预览请以根路径重新构建，再启动服务器：

```sh
python3 scripts/build.py --base-path '' --site-url http://localhost:8000
python3 -m http.server 8000 --directory dist
```

打开 <http://localhost:8000/>；按 `Ctrl+C` 停止服务器。根路径预览构建不会修改内容源文件，正式部署仍使用 `/ai-daily` 路径。

## 内容维护

常规日报保存在 `content/issues/YYYY-MM-DD.json`。同日另发精选时，可使用 `YYYY-MM-DD-curated.json` 并设置相同的 `slug`，以保留既有页面与样刊。`status` 使用 `daily`、`curated` 或 `sample`；同日精选优先于样刊展示，后续日报按日期成为首页。可用 `featured_ids` 选择首页最多六条推荐，用 highlight 的 `story_id` 直达对应内容。

每条研究或讨论应给出可回查的来源、实际发布日期以及证据或局限；样刊和正式日报应在内容中明确区分。新增内容后，构建器负责生成网页、RSS 订阅文件以及可导入 Obsidian 的 Markdown（`dist/markdown/YYYY-MM-DD.md`）。每期页面提供“保存 Markdown”入口。

## 会议、博客、公众号与关键词

`content/radar.json` 保存信息源目录，覆盖机器学习、视觉、语言和机器人会议，企业与高校研究博客，以及中文公众号发现入口。`content/keywords.json` 保存中英关键词、研究问题和证据检查项；网站在“研究雷达”集中展示，首页提供精选入口。当前方向地图是持续跟踪清单，不是当天热度排名。

国内团队固定检查名单包括 DeepSeek、阿里 Qwen／通义、字节 Seed／豆包、智谱 GLM、月之暗面 Kimi、百度 ERNIE／文心、腾讯混元、MiniMax、阶跃星辰 StepFun，以及已有的高校和研究机构。关注原论文、技术报告、官方代码和模型发布、独立评测，按新增研究价值收录，不要求每天各家都有新闻。

选题围绕大模型与具身领域当下出现的新机制、新能力、新问题，以及研究者和开发者正在具体讨论的争点，每天按新增证据重新排序。模型控制机器人、机器人 OOD 泛化、RSI、世界模型、Agent、推理与后训练等都是候选方向；Gemini 4、RSI 或某个品牌没有固定首页席位，也不要求每日出现。公众号、技术博客和社区发现的重要线索应进入实际选题筛选，不能只加到来源目录。通用模型、具身推理模型与动作策略分别核验；国内团队的正式研究与媒体产业动向分别标注。

当自我改进成为当期话题时，跟踪模型权重、策略、训练数据、Agent 代码／工具／记忆、评测框架与改进程序到底哪一层发生了更新；结果改进、持久的系统改进和改进机制本身的演化分别解释。检查每轮收益、总计算及人工投入、独立留出任务、验证器可靠性和第三方复现。自训练、反思、失败数据回流有实际价值，但这些标签本身不证明递归改进或加速；某篇论文的分级框架也不当作全行业统一标准。

具身方向重点跟踪小鹏 XPENG 的智能驾驶模型、VLA、世界模型、数据闭环和机器人／IRON 进展。记录版本、测试场景、人工干预、成功率、延迟及开放程度；未披露的数据明确说明，官方演示与第三方实测分别表述。重点公众号包括“具身智能之心”和“human five”（微信号 How-to-AI），同时关注机器之心、量子位、PaperWeekly、AI科技评论、新智元，从公开文章发现线索后回查原始研究；未核验的公众号入口不编造链接。human five 的用户指定入口是[《Gemini 4 Argon for Robotics》](https://mp.weixin.qq.com/s/c6jtVqfZ0bI3JtCtExzlhg)，已核对账号、正文及2026-10-14 08:00（北京时间）发布时间；原文未贴官方出处；现已独立读到 Google 官方总发布、机器人产品页与安全报告，此前已纳入具身选题，作为带日期的历史案例保留，不形成后续日报的固定主题。机器人专篇正文访问超时的具体指标仍待核验，不能用公众号转述替代官方证据。单篇文章不代表已覆盖该账号全部更新。

小鹏必须同时检查 GroundingPI / GroundAnything 的作者项目、论文、GitHub 与模型入口；两者为不同研究。企业资讯与产品页仅是辅助渠道，旧 X-Foresight 解读不能替代新的具身感知成果。国内具身固定名单包括智元 AgiBot、银河通用 Galbot、星海图 GALAXEA、星动纪元 Robotera、自变量 X Square、千寻智能 Spirit AI、宇树 Unitree、傅利叶 Fourier、优必选 UBTECH、逐际动力 LimX、帕西尼 PaXini、它石智航 TARS、蚂蚁灵波 Robbyant。星海图和星动纪元不能混用；论文归属逐篇核对，不将合作实验室全部工作计为公司成果。

每次采集先检查公司研究目录、作者项目、官方代码组织、模型／数据卡，再用中英文别名、作者机构和具身关键词搜索论文与公开媒体。`channels` 保存具体渠道的 `label`、`url`、`kind`、`status`、`checked_on`、`note`；`aliases` / `watch_terms` 用于补查，`evidence` 留归属及日期线索。`content_verified` 表示已读该具体内容，`reachable` 仅表示入口可达，`unreadable` / `unverified` 说明缺口；旧 `verified` 兼容显示为入口可达。HTTP 200、动态网页空壳或文章重定向首页均不证明读取了研究。公开模型链接也不证明完整训练和动作适配器已发布。

在临时采集记录中留下每家检查的页面、最新可核事件、未读渠道与补查结果。没有可核新增内容时不凑数；匿名媒体产业消息可进入产业观察，须在标题或标签明示未获官方确认，并回查原报道。同一原文的转载不能算独立佐证。弃用更新时间停在 2018 年的新浪旧 rollnews RSS；IT之家总 RSS 需筛选具身关键词并核验最新日期。

日报发现窗口建议设为最近 24–48 小时，遗漏内容可在 7 天内补充并注明原发布日期。顶会集中发布时追踪录用列表、OpenReview、论文集、代码与作者解读；旧论文因录用再次出现时注明“录用更新”，避免伪装成新论文。中文公众号、技术博客和社区讨论提供线索，再回查原论文或官方公告；没有核验到原始来源的说法应明确标注。

每期可添加 `keywords` 数组（`term`、`explanation`），生成网页与 Markdown 的“本期关键词”。日常关键词总结回答“什么方向出现新进展、大家在争论什么”；周度再总结重复出现的方向及依据。每个社区话题应写清讨论的具体问题、不同观点或可复现实验，保存原帖／作者博客／issue／评测等具体链接和日期，并说明它为什么值得关注。只有新论文或官方发布时标为“新研究／新发布”；声称“热门／社区热议”须另有实际讨论证据，注明观察窗口、去重方式与来源覆盖。同一原文的多次转载、单篇公众号文章、榜单排名或发布时间新，均不能自动证明热度或行业共识。技术价值与社区关注度分别判断，没有足够讨论证据时如实标注。

`content/recent-signals.json` 单独记录近期研究动向的日期窗口、具体来源、关键词和局限。它与历史代表论文构成的研究方向地图分别展示，更新时应移动日期窗口并重新核验来源，避免把过去的样本一直标为“最近”。

## 每日技术点

新日报每期讲一个当前重要、仍在主流模型或研究流程中使用的机制，优先联系当期新闻。可覆盖 GQA／MLA、KV cache、FlashAttention、MoE 路由、LoRA、DPO／GRPO／RLVR、流匹配、VLA 与机器人评测；不只追逐刚提出但尚无实践证据的方法，也避免反复讲已经退出主流的路线。原理来源可能早于新闻，明确其日期与当前用途，不把基础讲解称为今日新发现。检查近 30 期，避免主题机械重复。

使用可选 `technical_explainer` 字段，包含 `id`、`title`、`summary`、`reading_minutes`、`why_now`、`sections`（`heading` / `paragraphs` / 可选 `bullets`）、可选 `comparison` 表格（`caption` / `columns` / `rows`）、可选 `example`（`title` / `paragraphs`）、`checklist`、`takeaway` 和 `sources`（`label` / `url`）。建议 5–8 分钟：先说解决什么问题，再解释工作过程、一个直观例子、常见误读和阅读检查项，最后链接 2–4 个原始材料。假设算例明确标注，不冒充实测。首页提供入口，当期固定锚点为 `#technical-explainer`；全文同步到 RSS 所指网页和 Obsidian Markdown。旧刊没有该字段时保持可构建。

## 首次发布到 GitHub Pages

1. 使用 `trimason` 账户在 GitHub 新建公开仓库 `ai-daily`。创建时可选择空仓库，避免与本地已有 README 冲突。
2. 将这个独立项目目录推送到该仓库的 `main` 分支。请确认操作目录是 `ai-daily`，不要把上级论文库整体提交到公开仓库。
3. 在仓库的 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
4. 推送 `main` 后，或在 **Actions → Deploy GitHub Pages → Run workflow** 手动启动部署。
5. 工作流成功后，通过环境 `github-pages` 提供的链接访问网站；预期地址为 <https://trimason.github.io/ai-daily/>。

`.github/workflows/pages.yml` 会检出仓库、运行 Python 构建器，将 `dist/` 上传并发布。后续推送到 `main` 会再次部署，因此每期历史页面都能保留固定链接。

## 每日更新与网站部署

GitHub Actions 负责构建并发布仓库中的内容。采集、筛选、核验和中文写作由 Codex 的每日任务完成；网站本身没有内置模型 API，也不在浏览器中保存任何密钥。日常流程是核验原始来源、更新 JSON、构建、同步 Markdown、提交公开源码、检查 Pages 部署。

GitHub CLI 登录后，可用发布脚本检查变更。默认只检查，添加 `--publish` 才会提交到固定仓库 `trimason/ai-daily`：

```sh
python3 scripts/publish.py
python3 scripts/publish.py --publish
```

发布脚本使用 GitHub 官方 API，仅上传允许的内容和网站源码；不会上传 `dist/`、父目录论文库或凭据。如果远程在发布期间被更新，它会终止，避免覆盖并行变更。提交成功与网页部署成功分别核验。

## Obsidian 同步

构建后，可将 Markdown 复制到已有 Obsidian 库中的 `AI前沿日报/`。把命令中的路径替换成自己的库路径：

```sh
python3 scripts/sync_obsidian.py --vault /path/to/your/vault
```

同步仅管理独立日报目录中的日期笔记；个人笔记保存在其他文件，已有非日报文件不会被覆盖。这里的笔记留在本地，不会提交到公开仓库。同日精选使用带后缀的独立笔记名，保留已有样刊；正式每日任务继续生成新日期的日报。
