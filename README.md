# AI 前沿日报

面向中文阅读的大模型与具身智能研究日报网站。每期保留独立链接，提供历史归档和 RSS，适合在电脑和手机上阅读。

网站：<https://trimason.github.io/ai-daily/>。源码仓库：<https://github.com/trimason/ai-daily>。

当前内容是用于确认网站结构和阅读体验的样刊，**不代表对应日期的完整新闻汇总**。各条内容的实际发布日期、来源与核验说明见正文。

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

每期内容保存在 `content/issues/YYYY-MM-DD.json`，例如 `content/issues/2026-10-14.json`。以已有样刊的字段结构为模板，新增日期对应的 JSON，再运行构建命令。

每条研究或讨论应给出可回查的来源、实际发布日期以及证据或局限；样刊和正式日报应在内容中明确区分。新增内容后，构建器负责生成网页、RSS 订阅文件以及可导入 Obsidian 的 Markdown（`dist/markdown/YYYY-MM-DD.md`）。每期页面提供“保存 Markdown”入口。

## 会议、博客、公众号与关键词

`content/radar.json` 保存信息源目录，覆盖机器学习、视觉、语言和机器人会议，企业与高校研究博客，以及中文公众号发现入口。`content/keywords.json` 保存中英关键词、研究问题和证据检查项；网站在“研究雷达”集中展示，首页提供精选入口。当前方向地图是持续跟踪清单，不是当天热度排名。

国内团队固定检查名单包括 DeepSeek、阿里 Qwen／通义、字节 Seed／豆包、智谱 GLM、月之暗面 Kimi、百度 ERNIE／文心、腾讯混元、MiniMax、阶跃星辰 StepFun，以及已有的高校和研究机构。关注原论文、技术报告、官方代码和模型发布、独立评测，按新增研究价值收录，不要求每天各家都有新闻。

具身方向重点跟踪小鹏 XPENG 的智能驾驶模型、VLA、世界模型、数据闭环和机器人／IRON 进展。记录版本、测试场景、人工干预、成功率、延迟及开放程度；未披露的数据明确说明，官方演示与第三方实测分别表述。公众号加入“具身智能之心”，从公开可访问文章发现线索后回查原始研究；未核验的公众号入口不编造链接。

日报发现窗口建议设为最近 24–48 小时，遗漏内容可在 7 天内补充并注明原发布日期。顶会集中发布时追踪录用列表、OpenReview、论文集、代码与作者解读；旧论文因录用再次出现时注明“录用更新”，避免伪装成新论文。中文公众号、技术博客和社区讨论提供线索，再回查原论文或官方公告；没有核验到原始来源的说法应明确标注。

每期可添加 `keywords` 数组（`term`、`explanation`），生成网页与 Markdown 的“本期关键词”。日常关键词总结回答“什么方向出现新进展、大家在争论什么”；周度再总结重复出现的方向及依据。热度需注明观察窗口、去重方式与来源覆盖，不凭单篇报道得出行业趋势。

`content/recent-signals.json` 单独记录近期研究动向的日期窗口、具体来源、关键词和局限。它与历史代表论文构成的研究方向地图分别展示，更新时应移动日期窗口并重新核验来源，避免把过去的样本一直标为“最近”。

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

同步仅管理独立日报目录中的日期笔记；个人笔记保存在其他文件，已有非日报文件不会被覆盖。这里的笔记留在本地，不会提交到公开仓库。当前一期仍是明确标注的样刊；正式每日任务会生成新日期的日报。
