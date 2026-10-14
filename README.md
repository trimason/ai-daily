# AI 前沿日报

面向中文阅读的大模型与具身智能研究日报网站。每期保留独立链接，提供历史归档和 RSS，适合在电脑和手机上阅读。

计划地址：<https://trimason.github.io/ai-daily/>。该地址在创建仓库、启用 GitHub Pages 并成功部署后才会生效。

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

## 每日生成与网站部署

目前工作流只负责发布仓库中已有的内容，**尚未启用每天自动采集和生成新闻**。网站托管与新闻生成是两个独立环节。

新闻自动生成需要进一步确定信息源、采集方式、去重记录、模型 API、生成时间和质量检查，再配置相应的定时流程。所需 API 密钥应保存在 GitHub Secrets 等密钥存储中，不写入公开仓库，也不放入日报内容。

在采集与生成流程完成前，可以人工维护 `content/issues/` 并通过现有工作流发布。公开仓库及 GitHub Pages 会公开展示提交的内容，请仅放入计划公开的日报与网站文件。
