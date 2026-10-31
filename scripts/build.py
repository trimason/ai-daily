#!/usr/bin/env python3
"""Build a small, dependency-free Chinese research digest website."""
import argparse
import html
import json
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {"llm": "大模型", "embodied": "具身智能", "discussion": "前沿讨论"}
BASE = ""
SITE = ""
VERIFICATION_LABELS = {
    "content_verified": "内容已核验",
    "verified": "入口可达",
    "reachable": "入口可达",
    "unreadable": "本次未能读取",
    "unverified": "待核验",
}


def esc(value):
    return html.escape(str(value or ""), quote=True)


def href(path=""):
    return BASE + "/" + path.lstrip("/")


def url(value):
    if not isinstance(value, str):
        raise ValueError(f"Invalid source URL: {value}")
    parsed = urlparse(value)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError(f"Invalid source URL: {value}")
    return esc(value)


def display_date(value):
    d = date.fromisoformat(value)
    return f"{d.year} 年 {d.month} 月 {d.day} 日"


def issue_path(issue):
    return f"daily/{issue.get('slug', issue['date'])}/"


def label(issue):
    if issue.get('status') == 'sample':
        return '<span class="sample-badge">样刊</span>'
    if issue.get('status') == 'curated':
        return '<span class="sample-badge live">精选</span>'
    return '<span class="sample-badge live">日报</span>'


def layout(title, body, active="home", description="每日关注大模型、具身智能与研究社区的前沿进展。", canonical=""):
    nav = [("home", "", "最新日报"), ("archive", "archive/", "历史归档"), ("topics", "topics/", "主题检索"), ("radar", "radar/", "研究雷达"), ("about", "about/", "关于简报")]
    links = []
    for key, path, name in nav:
        current = 'aria-current="page"' if key == active else ''
        links.append(f'<a href="{href(path)}" {current}>{name}</a>')
    links = ''.join(links)
    canon = f'<link rel="canonical" href="{esc(SITE + "/" + canonical)}">' if SITE else ""
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · 前沿日课</title>
  <meta name="description" content="{esc(description)}"><meta name="theme-color" content="#f7f8f4">
  <meta property="og:title" content="{esc(title)} · 前沿日课"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="website">
  {canon}
  <link rel="icon" href="{href('assets/favicon.svg')}" type="image/svg+xml">
  <link rel="stylesheet" href="{href('assets/style.css')}">
  <link rel="alternate" type="application/rss+xml" title="前沿日课 RSS" href="{href('feed.xml')}">
  <script src="{href('assets/app.js')}" defer></script>
</head>
<body>
  <a class="skip" href="#main">跳到正文</a>
  <header class="site-header"><div class="shell header-inner">
    <a class="brand" href="{href()}"><span class="brand-mark" aria-hidden="true"><i></i></span><span>前沿日课<small>FRONTIER DAILY</small></span></a>
    <nav aria-label="主导航">{links}</nav>
    <a class="rss-link" href="{href('feed.xml')}" aria-label="RSS 订阅">RSS <span aria-hidden="true">↗</span></a>
  </div></header>
  <main id="main" class="shell">{body}</main>
  <footer class="site-footer"><div class="shell footer-inner"><div><strong>前沿日课</strong><p>追踪研究，保留证据。</p></div><div class="footer-links"><a href="{href('about/')}">来源与方法</a><a href="{href('feed.xml')}">RSS 订阅 ↗</a><a href="https://github.com/trimason" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div><p class="footer-note">大模型 / 具身智能 / 前沿讨论</p></div></footer>
</body></html>'''


def teaser(story, issue):
    return f'''<a class="story-teaser" href="{href(issue_path(issue))}#{esc(story['id'])}">
      <div class="meta"><span class="tag {esc(story['category'])}">{esc(story.get('tag') or CATEGORIES[story['category']])}</span><span>{esc(story.get('organization'))}</span></div>
      <h3>{esc(story['title'])}</h3><div class="published">{esc(story.get('date_label', '来源发布日期'))}：{esc(story.get('published') or '待确认')}</div><p>{esc(story['summary'])}</p><span class="read-link">查看研究与来源 <span aria-hidden="true">↗</span></span>
    </a>'''


def archive_row(issue):
    counts = {k: sum(s['category'] == k for s in issue['stories']) for k in CATEGORIES}
    count_line = " · ".join(f"{CATEGORIES[k]} {n}" for k, n in counts.items() if n)
    return f'''<a class="archive-row" href="{href(issue_path(issue))}"><time datetime="{issue['date']}">{issue['date'].replace('-', '.')}</time><div><h3>{esc(issue['title'])} {label(issue)}</h3><p>{esc(count_line)}</p></div><span aria-hidden="true">↗</span></a>'''


def signal_card(signal):
    tags = ''.join(f'<span>{esc(k)}</span>' for k in signal['keywords'])
    return f'<article class="signal-card" id="{esc(signal["id"])}"><div class="signal-meta"><time datetime="{esc(signal["published"])}">{esc(signal["published"])}</time><span>{esc(signal["source_label"])}</span></div><h3><a href="{url(signal["url"])}" target="_blank" rel="noopener noreferrer">{esc(signal["title"])} ↗</a></h3><p>{esc(signal["summary"])}</p><div class="keyword-tags">{tags}</div><p class="signal-limitation"><strong>如何理解：</strong>{esc(signal["limitation"])}</p></article>'


def technical_preview(issue):
    lesson = issue.get('technical_explainer')
    if not lesson:
        return ''
    return f'<section class="technical-preview"><div><p class="eyebrow">DAILY MECHANISM · {lesson["reading_minutes"]} 分钟</p><h2>每日技术点：{esc(lesson["title"])}</h2><p class="technical-preview-summary">{esc(lesson["summary"])}</p></div><a class="quiet-link" href="{href(issue_path(issue))}#technical-explainer">读懂机制 →</a></section>'


def research_preview(issue):
    supplement = issue.get('research_supplement')
    if not supplement:
        return ''
    return f'<section class="technical-preview"><div><p class="eyebrow">RESEARCH SUPPLEMENT · 全文约 {supplement["reading_minutes"]} 分钟</p><h2>专题追踪：{esc(supplement["title"])}</h2><p class="technical-preview-summary">{esc(supplement["summary"])}</p></div><a class="quiet-link" href="{href(issue_path(issue))}#research-supplement">阅读专题 →</a></section>'


def technical_explainer(lesson, *, section_id='technical-explainer', section_title='每日技术点'):
    section_html = []
    for section in lesson['sections']:
        paragraphs = ''.join(f'<p>{esc(text)}</p>' for text in section['paragraphs'])
        bullets = f'<ul>{"".join(f"<li>{esc(text)}</li>" for text in section["bullets"])}</ul>' if section.get('bullets') else ''
        section_html.append(f'<div class="lesson-section"><h4>{esc(section["heading"])}</h4>{paragraphs}{bullets}</div>')
    comparison_html = ''
    if lesson.get('comparison'):
        comparison = lesson['comparison']
        columns = ''.join(f'<th scope="col">{esc(text)}</th>' for text in comparison['columns'])
        rows = ''.join('<tr>' + ''.join(f'<td>{esc(text)}</td>' for text in row) + '</tr>' for row in comparison['rows'])
        comparison_html = f'<div class="lesson-table-scroll" tabindex="0" role="region" aria-label="{esc(comparison["caption"])}"><table class="lesson-table"><caption>{esc(comparison["caption"])}</caption><thead><tr>{columns}</tr></thead><tbody>{rows}</tbody></table></div>'
    example_html = ''
    if lesson.get('example'):
        example = lesson['example']
        paragraphs = ''.join(f'<p>{esc(text)}</p>' for text in example['paragraphs'])
        example_html = f'<div class="lesson-example"><h4>{esc(example["title"])}</h4>{paragraphs}</div>'
    checklist = ''.join(f'<li>{esc(text)}</li>' for text in lesson['checklist'])
    sources = ''.join(f'<a href="{url(source["url"])}" target="_blank" rel="noopener noreferrer">{esc(source["label"])} ↗</a>' for source in lesson['sources'])
    is_supplement = section_id == 'research-supplement'
    why_heading = '为什么今天补充' if is_supplement else '为什么今天讲这个'
    checklist_heading = '核验时检查这些' if is_supplement else '读论文时检查这些'
    reading_label = '全文约' if is_supplement else ''
    reading_suffix = '分钟' if is_supplement else '分钟理解'
    return f'<section class="article-section technical-explainer" id="{esc(section_id)}"><div class="article-section-title"><h2>{esc(section_title)}</h2><span>{reading_label}{lesson["reading_minutes"]} {reading_suffix}</span></div><article class="technical-lesson" data-explainer-id="{esc(lesson["id"])}"><h3>{esc(lesson["title"])}</h3><p class="lesson-summary">{esc(lesson["summary"])}</p><div class="lesson-why"><h4>{why_heading}</h4><p>{esc(lesson["why_now"])}</p></div>{"".join(section_html)}{comparison_html}{example_html}<div class="lesson-section"><h4>{checklist_heading}</h4><ul class="lesson-checklist">{checklist}</ul></div><p class="lesson-takeaway"><strong>带走一句话：</strong>{esc(lesson["takeaway"])}</p><div class="source-links"><span>来源与证据</span>{sources}</div></article></section>'


def home(issues, keywords, recent):
    latest = issues[0]
    stories = latest['stories']
    highlights = latest.get('highlights', [])[:3]
    cards = "".join(f'<a class="highlight-card" href="{href(issue_path(latest))}{("#" + esc(h["story_id"])) if h.get("story_id") else ""}"><span class="highlight-number">0{i + 1}</span><h3>{esc(h["title"])}</h3><p>{esc(h["text"])}</p><span aria-hidden="true" class="highlight-arrow">↗</span></a>' for i, h in enumerate(highlights))
    if latest.get('featured_ids'):
        by_id = {s['id']: s for s in stories}
        picks = [by_id[story_id] for story_id in latest['featured_ids']]
    else:
        picks = []
        for category in CATEGORIES:
            picks += [s for s in stories if s['category'] == category][:2]
    reading = latest.get('reading', [])
    reading_html = "".join(f'<a class="reading-item" href="{url(r["url"])}" target="_blank" rel="noopener noreferrer"><span>↗</span><div><h3>{esc(r["title"])}</h3><p>{esc(r["reason"])}</p></div></a>' for r in reading)
    reading_panel = f'<section class="side-panel reading-panel"><p class="eyebrow">READ NEXT</p><h2>值得深入读</h2>{reading_html}</section>' if reading else ""
    direction_cards = ''.join(f'<a class="direction-preview" href="{href("radar/")}#{esc(d["id"])}"><h3>{esc(d["title"])}</h3><p>{esc(d["explanation"])}</p><span>{esc(" · ".join(d["keywords_en"][:3]))}</span></a>' for d in keywords['directions'][:6])
    direction_panel = f'<section class="direction-section"><div class="section-heading"><div><p class="eyebrow">FOLLOW THE QUESTIONS</p><h2>持续跟踪的研究方向</h2></div><a class="quiet-link" href="{href("radar/")}#directions">关键词与信息源 →</a></div><p class="direction-intro">{esc(keywords["metadata"]["intro"])}</p><div class="direction-preview-grid">{direction_cards}</div></section>'
    recent_panel = f'<section class="direction-section"><div class="section-heading"><div><p class="eyebrow">WHAT IS MOVING</p><h2>近期研究动向</h2></div><a class="quiet-link" href="{href("radar/")}#recent-signals">查看全部动向 →</a></div><p class="direction-intro">{esc(recent["intro"])}</p><div class="signal-grid">{"".join(signal_card(s) for s in recent["signals"][:3])}</div></section>'
    body = f'''
    <section class="hero">
      <div class="hero-copy"><p class="eyebrow"><span class="status-dot"></span> AI RESEARCH BRIEFING</p><h1>大模型与具身智能，<br>每日研究简报<span class="period">。</span></h1><p class="hero-description">从新论文、研究成果到前沿争论，<br class="desktop-break">读懂发生了什么，也看清证据与局限。</p><div class="hero-actions"><a class="button primary" href="{href(issue_path(latest))}">阅读最新一期 <span aria-hidden="true">↗</span></a><a class="quiet-link" href="{href('archive/')}">浏览历史 <span aria-hidden="true">→</span></a></div><div class="hero-topics"><span>大模型</span><span>具身智能</span><span>前沿讨论</span></div></div>
      <aside class="issue-cover"><div class="cover-top"><span>LATEST ISSUE</span>{label(latest)}</div><div class="cover-date"><span>{date.fromisoformat(latest['date']).strftime('%m')}</span><b>/</b><span>{date.fromisoformat(latest['date']).strftime('%d')}</span><small>{latest['date'][:4]}</small></div><h2>{esc(latest['title'])}</h2><p>{esc(latest['intro'])}</p><a href="{href(issue_path(latest))}">打开本期简报 <span aria-hidden="true">↗</span></a></aside>
    </section>
    <div class="coverage-note"><span aria-hidden="true">◌</span><p>{esc(latest.get('coverage', '以公开来源为依据，记录研究进展与社区讨论。'))}</p></div>
    <section class="highlights"><div class="section-heading"><div><p class="eyebrow">THE SHORTLIST</p><h2>本期速读</h2></div><span class="section-hint">先看重点，再读原文</span></div><div class="highlight-grid">{cards}</div></section>
    {research_preview(latest)}
    {technical_preview(latest)}
    <div class="content-columns"><section><div class="section-heading"><div><p class="eyebrow">RESEARCH & IDEAS</p><h2>研究与观点</h2></div><a class="quiet-link" href="{href('topics/')}">按主题检索 →</a></div><div class="teaser-list">{''.join(teaser(s, latest) for s in picks)}</div></section><aside class="sidebar">{reading_panel}<section class="side-panel"><p class="eyebrow">HOW TO READ</p><h2>每条都能追溯</h2><ul class="method-list"><li><span>01</span>新成果与新贡献</li><li><span>02</span>为什么值得关注</li><li><span>03</span>实验局限与原始来源</li></ul><a class="quiet-link" href="{href('about/')}">了解筛选方法 →</a></section><section class="subscribe-panel"><span class="eyebrow">STAY CURIOUS</span><h2>把更新放进阅读器</h2><p>通过 RSS 订阅，保留自己的阅读节奏。</p><a href="{href('feed.xml')}">RSS 订阅 ↗</a></section></aside></div>
    {recent_panel}
    {direction_panel}
    <section class="recent"><div class="section-heading"><div><p class="eyebrow">THE ARCHIVE</p><h2>近期简报</h2></div><a class="quiet-link" href="{href('archive/')}">全部归档 →</a></div>{''.join(archive_row(i) for i in issues[:5])}</section>'''
    return layout("最新日报", body)


def article(story):
    published = display_date(story['published']) if story.get('published') else "发布日期待确认"
    sources = "".join(f'<a href="{url(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["label"])} ↗</a>' for s in story['sources'])
    return f'''<article class="research-card" id="{esc(story['id'])}"><div class="meta"><span class="tag {esc(story['category'])}">{esc(story.get('tag') or CATEGORIES[story['category']])}</span><span>{esc(story.get('organization'))}</span></div><h3>{esc(story['title'])}</h3><div class="published">{esc(story.get('date_label', '来源发布日期'))}：{esc(published)}</div><p class="story-summary">{esc(story['summary'])}</p><div class="analysis-grid"><div><h4><span class="green-dot"></span>为什么关注</h4><p>{esc(story['why'])}</p></div><div><h4><span class="amber-dot"></span>证据与局限</h4><p>{esc(story['limitation'])}</p></div></div><div class="source-links"><span>来源与证据</span>{sources}</div></article>'''


def daily(issue, issues):
    toc = []
    sections = []
    if issue.get('research_supplement'):
        toc.append('<a href="#research-supplement">专题追踪<span>↗</span></a>')
        sections.append(technical_explainer(issue['research_supplement'], section_id='research-supplement', section_title='专题追踪 · 当日补充研究'))
    for key, name in CATEGORIES.items():
        stories = [s for s in issue['stories'] if s['category'] == key]
        if not stories:
            continue
        toc.append(f'<a href="#section-{key}">{name}<span>{len(stories):02d}</span></a>')
        sections.append(f'<section class="article-section" id="section-{key}"><div class="article-section-title"><h2>{name}</h2><span>{len(stories):02d} 条</span></div>{"".join(article(s) for s in stories)}</section>')
    if issue.get('technical_explainer'):
        toc.append('<a href="#technical-explainer">每日技术点<span>↗</span></a>')
        sections.append(technical_explainer(issue['technical_explainer']))
    if issue.get('keywords'):
        toc.append('<a href="#issue-keywords">本期关键词<span>↗</span></a>')
        keyword_rows = ''.join(f'<div class="issue-keyword"><h3>{esc(k["term"])}</h3><p>{esc(k["explanation"])}</p></div>' for k in issue['keywords'])
        sections.append(f'<section class="article-section" id="issue-keywords"><div class="article-section-title"><h2>本期关键词</h2><a class="quiet-link" href="{href("radar/")}">研究方向地图 →</a></div><p class="keyword-scope">关键词来自本期收录内容，帮助检索与理解。</p><div class="issue-keywords">{keyword_rows}</div></section>')
    idx = issues.index(issue)
    previous = f'<a href="{href(issue_path(issues[idx + 1]))}">← 上一期 · {issues[idx + 1]["date"]}</a>' if idx + 1 < len(issues) else '<span>归档从本期开始</span>'
    body = f'''<div class="article-heading"><a class="back-link" href="{href()}">← 返回首页</a><div class="issue-meta"><time datetime="{issue['date']}">{display_date(issue['date'])}</time>{label(issue)}<span>{len(issue['stories'])} 条精选</span><a href="{href('markdown/' + issue.get('slug', issue['date']) + '.md')}" download>保存 Markdown ↓</a></div><h1>{esc(issue['title'])}</h1><p>{esc(issue['intro'])}</p></div><div class="coverage-note"><span aria-hidden="true">◌</span><p>{esc(issue.get('coverage'))}</p></div><div class="article-layout"><aside class="article-toc"><p class="eyebrow">本期目录</p>{''.join(toc)}<a class="toc-archive" href="{href('archive/')}">历史归档 ↗</a></aside><div class="article-body">{''.join(sections)}<div class="issue-navigation">{previous}<a href="{href('archive/')}">全部简报 →</a></div></div></div>'''
    return layout(issue['title'], body, description=issue['intro'], canonical=issue_path(issue))


def markdown_text(value):
    return re.sub(r'([\\`*_{}\[\]#|])', r'\\\1', html.escape(str(value), quote=False))


def technical_markdown(lesson, *, section_title='每日技术点', section_id='technical-explainer'):
    def paragraphs(items):
        return [line for text in items for line in [markdown_text(text), '']]

    is_supplement = section_title != '每日技术点'
    why_heading = '为什么今天补充' if is_supplement else '为什么今天讲这个'
    checklist_heading = '核验时检查这些' if is_supplement else '读论文时检查这些'
    lines = [f'<a id="{esc(section_id)}"></a>', '', f'## {markdown_text(section_title)}：{markdown_text(lesson["title"])}', '', f'阅读时间：{lesson["reading_minutes"]} 分钟', '', markdown_text(lesson['summary']), '', f'**{why_heading}**', '', markdown_text(lesson['why_now']), '']
    for section in lesson['sections']:
        lines += [f'### {markdown_text(section["heading"])}', '']
        lines += paragraphs(section['paragraphs'])
        if section.get('bullets'):
            lines += [f'- {markdown_text(text)}' for text in section['bullets']] + ['']
    if lesson.get('comparison'):
        comparison = lesson['comparison']
        cell = lambda text: markdown_text(text).replace('\n', '<br>')
        lines += [f'**{markdown_text(comparison["caption"])}**', '', '| ' + ' | '.join(cell(text) for text in comparison['columns']) + ' |', '| ' + ' | '.join('---' for _ in comparison['columns']) + ' |']
        lines += ['| ' + ' | '.join(cell(text) for text in row) + ' |' for row in comparison['rows']]
        lines += ['']
    if lesson.get('example'):
        lines += [f'### {markdown_text(lesson["example"]["title"])}', '']
        lines += paragraphs(lesson['example']['paragraphs'])
    lines += [f'### {checklist_heading}', ''] + [f'- {markdown_text(text)}' for text in lesson['checklist']]
    lines += ['', '**带走一句话**', '', markdown_text(lesson['takeaway']), '', '**来源与证据**', '']
    lines += [f'- [{markdown_text(source["label"])}](<{source["url"]}>)' for source in lesson['sources']]
    return lines + ['']


def markdown(issue):
    edition = {'sample': ' · 样刊', 'curated': ' · 精选'}.get(issue.get('status'), '')
    lines = [f'# {issue["title"]}', '', f'日期：{issue["date"]}' + edition, '', issue['coverage'], '', issue['intro'], '']
    if issue.get('research_supplement'):
        lines += technical_markdown(issue['research_supplement'], section_title='专题追踪 · 当日补充研究', section_id='research-supplement')
    for key, name in CATEGORIES.items():
        stories = [s for s in issue['stories'] if s['category'] == key]
        if not stories:
            continue
        lines += [f'## {name}', '']
        for s in stories:
            lines += [f'### {s["title"]}', '', f'{s["organization"]} · {s.get("date_label", "来源发布日期")}：{s.get("published") or "待确认"}', '', s['summary'], '', '**为什么关注**', '', s['why'], '', '**证据与局限**', '', s['limitation'], '', '**来源与证据**', '']
            lines += [f'- [{source["label"]}]({source["url"]})' for source in s['sources']]
            lines += ['']
    if issue.get('technical_explainer'):
        lines += technical_markdown(issue['technical_explainer'])
    if issue.get('keywords'):
        lines += ['## 本期关键词', '', '关键词来自本期收录内容，帮助检索与理解。', '']
        for keyword in issue['keywords']:
            lines += [f'- **{keyword["term"]}**：{keyword["explanation"]}']
        lines += ['']
    return '\n'.join(lines)


def archives(issues):
    body = f'''<section class="page-heading"><p class="eyebrow">THE ARCHIVE</p><h1>每天一页，持续追踪。</h1><p>沿着时间，回看大模型与具身智能的研究进展。</p></section><div class="archive-summary"><strong>{len(issues):02d}</strong><span>期简报</span><span class="archive-start">始于 {issues[-1]['date']}</span></div><section class="archive-list">{''.join(archive_row(i) for i in issues)}</section>'''
    return layout("历史归档", body, "archive", canonical="archive/")


def topics(issues):
    all_stories = [(s, i) for i in issues for s in i['stories']]
    filters = '<button type="button" class="filter-button selected" data-filter="all" aria-pressed="true">全部</button>' + "".join(f'<button type="button" class="filter-button" data-filter="{k}" aria-pressed="false">{name}</button>' for k, name in CATEGORIES.items())
    cards = []
    for s, i in all_stories:
        searchable = " ".join(str(s.get(k) or "") for k in ['title', 'organization', 'summary', 'tag']) + " " + CATEGORIES[s['category']] + " " + i['date']
        cards.append(f'<div class="search-item" data-category="{s["category"]}" data-search="{esc(searchable.lower())}"><div class="search-date">{i["date"]} {label(i)}</div>{teaser(s, i)}</div>')
    body = f'''<section class="page-heading"><p class="eyebrow">EXPLORE THE FRONTIER</p><h1>沿着问题，找到研究。</h1><p>按方向筛选，或搜索论文、机构与关键词。</p></section><section class="search-panel"><label class="search-label" for="search-input">搜索全部简报</label><div class="search-box"><span aria-hidden="true">⌕</span><input id="search-input" type="search" placeholder="试试 VLA、推理、Stanford…" autocomplete="off"></div><div class="filters" aria-label="按主题筛选">{filters}</div></section><p class="results-count" aria-live="polite"><span id="result-count">{len(cards)}</span> 条内容</p><div class="search-results">{''.join(cards)}</div><div class="empty-results" id="empty-results" hidden><h2>暂时没有匹配的内容</h2><p>试试其他关键词，或切换到“全部”。</p></div><noscript><p>关闭 JavaScript 时仍可浏览全部条目；搜索与主题筛选需要启用 JavaScript。</p></noscript>'''
    return layout("主题检索", body, "topics", canonical="topics/")


def about():
    body = '''<section class="page-heading"><p class="eyebrow">SOURCES & METHOD</p><h1>关注进展，也关注证据。</h1><p>一份面向研究阅读的大模型与具身智能简报。</p></section><div class="about-grid"><section class="about-card"><span class="about-number">01</span><h2>一手来源优先</h2><p>从企业与实验室公告、论文、代码和项目页追踪成果。社区讨论用于发现问题与分歧，保留具体出处。</p></section><section class="about-card"><span class="about-number">02</span><h2>两条研究主线</h2><p>大模型关注推理、Agent、多模态、训练与评测；具身智能关注 VLA、世界模型、机器人学习与真实部署。</p></section><section class="about-card"><span class="about-number">03</span><h2>贡献与局限一起读</h2><p>记录新贡献、研究意义及证据边界。机构自报、独立复现和社区观点分别表述，未核验的部分明确标注。</p></section><section class="about-card"><span class="about-number">04</span><h2>保留准确的时间线</h2><p>简报日期与来源发布日期分别展示。旧论文的新代码、复现或评测若再次收录，会说明本次更新的原因。</p></section></div><section class="about-note"><h2>区分日报、精选与样刊</h2><p>日报筛选近期新增内容；精选按研究价值推荐，可包含明确标注日期的历史读物；样刊展示阅读体验。每条分别记录来源日期与简报整理日期，不把历史成果当作当天新发布。</p><p>本网站提供历史归档、主题检索与 RSS。订阅 RSS 可在支持的阅读器中查看后续更新。</p></section>'''
    return layout("来源与方法", body, "about", canonical="about/")


def verification_badge(verification, channel=False):
    status = verification.get('status', 'unverified')
    label_text = VERIFICATION_LABELS[status]
    if channel and status in ('verified', 'reachable'):
        label_text = '链接可达'
    checked = f'<time datetime="{esc(verification["checked_on"])}">{esc(verification["checked_on"])}</time>' if verification.get('checked_on') else ''
    # Legacy "verified" recorded HTTP connectivity, not publication verification.
    css_status = 'reachable' if status == 'verified' else status
    return f'<span class="verification-status {esc(css_status)}">{esc(label_text)}</span>{checked}'


def radar_source(source):
    name = f'<a href="{url(source["url"])}" target="_blank" rel="noopener noreferrer">{esc(source["name"])} ↗</a>' if source.get('url') else esc(source['name'])
    verification = source.get('verification', {})
    status = f'<div class="source-verification"><span>主入口</span>{verification_badge(verification)}</div>'
    notes = [source.get('note'), verification.get('note')]
    note_html = ''.join(f'<p class="source-note">{esc(note)}</p>' for note in dict.fromkeys(n for n in notes if n))
    channels = []
    for channel in source.get('channels', []):
        channel_note = f'<p>{esc(channel["note"])}</p>' if channel.get('note') else ''
        channels.append(f'<li><a href="{url(channel["url"])}" target="_blank" rel="noopener noreferrer">{esc(channel["label"])} ↗</a><div class="channel-verification">{verification_badge(channel, channel=True)}</div>{channel_note}</li>')
    channel_html = f'<div class="source-channels"><h4>跟进渠道</h4><ul>{"".join(channels)}</ul></div>' if channels else ''
    search_terms = []
    if source.get('aliases'):
        search_terms.append(f'<p><strong>别名：</strong>{esc(" / ".join(source["aliases"]))}</p>')
    if source.get('watch_terms'):
        search_terms.append(f'<p><strong>检索词：</strong>{esc(" · ".join(source["watch_terms"]))}</p>')
    evidence = []
    for item in source.get('evidence', []):
        date_text = f' · {esc(item["published"])}' if item.get('published') else ''
        basis = f'<span>{esc(item["date_basis"])}</span>' if item.get('date_basis') else ''
        evidence.append(f'<li><a href="{url(item["url"])}" target="_blank" rel="noopener noreferrer">{esc(item["label"])}{date_text} ↗</a>{basis}</li>')
    evidence_html = f'<h4>核验线索</h4><ul>{"".join(evidence)}</ul>' if evidence else ''
    detail_html = f'<details class="source-research-details"><summary>检索词与核验线索</summary>{"".join(search_terms)}{evidence_html}</details>' if search_terms or evidence else ''
    return f'<article class="radar-source" id="{esc(source["id"])}"><h3>{name}</h3>{status}<p>{esc(source["role"])}</p><p class="source-detail">{esc(source.get("scope"))}</p>{note_html}{channel_html}{detail_html}</article>'


def research_radar(radar, keywords, recent):
    directions = []
    for direction in keywords['directions']:
        tags = ''.join(f'<span>{esc(k)}</span>' for k in direction['keywords_zh'] + direction['keywords_en'])
        research = ''.join(f'<li>{esc(item)}</li>' for item in direction['researchers_do'])
        evidence = ''.join(f'<li>{esc(item)}</li>' for item in direction['evidence_to_check'])
        sources = ''.join(f'<a href="{url(source["url"])}" target="_blank" rel="noopener noreferrer">{esc(source["label"])}{(" · " + esc(source["published"])) if source.get("published") else ""} ↗</a>' for source in direction['sources'])
        directions.append(f'<article class="direction-card" id="{esc(direction["id"])}"><h3>{esc(direction["title"])}</h3><div class="keyword-tags">{tags}</div><p class="direction-explanation">{esc(direction["explanation"])}</p><div class="analysis-grid"><div><h4>研究者在做什么</h4><ul>{research}</ul></div><div><h4>读成果时检查什么</h4><ul>{evidence}</ul></div></div><div class="source-links"><span>参考来源</span>{sources}</div></article>')
    groups = []
    for group in radar['groups']:
        rows = [radar_source(source) for source in group['sources']]
        groups.append(f'<section class="radar-group" id="{esc(group["id"])}"><div class="section-heading"><div><h2>{esc(group["group"])}</h2><p class="direction-intro">{esc(group["description"])}</p></div></div><div class="radar-sources">{"".join(rows)}</div></section>')
    rules = ''.join(f'<li>{esc(rule)}</li>' for rule in radar['selection_rules'])
    signals = f'<section id="recent-signals" class="radar-group"><div class="section-heading"><div><p class="eyebrow">WHAT IS MOVING</p><h2>{esc(recent["title"])}</h2><p class="direction-intro">{esc(recent["intro"])}</p></div></div><div class="signal-grid">{"".join(signal_card(s) for s in recent["signals"])}</div></section>'
    embodied_jump = '<a href="#domestic-embodied">国内具身公司 ↓</a>' if any(g['id'] == 'domestic-embodied' for g in radar['groups']) else ''
    body = f'<section class="page-heading"><p class="eyebrow">RESEARCH RADAR</p><h1>大家在研究什么，<br>从哪里跟进。</h1><p>用中英关键词追踪问题，用会议、实验室与研究社区找到线索。</p></section><div class="coverage-note"><span aria-hidden="true">◌</span><p>{esc(keywords["metadata"]["intro"])}</p></div><div class="radar-jump"><a href="#recent-signals">近期动向 ↓</a><a href="#directions">研究方向 ↓</a><a href="#sources">会议、博客与公众号 ↓</a><a href="#domestic-model-teams">国内大模型团队 ↓</a>{embodied_jump}<a href="#xpeng">XPENG 小鹏 ↓</a><a href="#chinese-media">中文公众号 ↓</a><a href="#selection">如何筛选 ↓</a></div>{signals}<section id="directions" class="radar-group"><div class="section-heading"><div><p class="eyebrow">KEYWORDS & QUESTIONS</p><h2>研究方向地图</h2></div></div><div class="direction-grid">{"".join(directions)}</div></section><section id="sources" class="radar-heading"><p class="eyebrow">WHERE TO LOOK</p><h2>{esc(radar["title"])}</h2><p class="direction-intro">{esc(radar["intro"])}</p><p class="verification-key">内容已核验：已读取具体页面；入口可达：已确认链接可访问。核验日期反映本次检查时间，不保证覆盖所有更新。</p></section>{"".join(groups)}<section class="about-note" id="selection"><h2>热点如何进入日报</h2><ol class="selection-rules">{rules}</ol></section>'
    return layout('研究雷达与关键词', body, 'radar', canonical='radar/')


def feed(issues):
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    for key, value in [("title", "前沿日课 · 大模型与具身智能"), ("link", SITE + "/"), ("description", "新论文、研究成果与前沿讨论，保留来源与证据。"), ("language", "zh-cn")]:
        ET.SubElement(channel, key).text = value
    for issue in issues:
        item = ET.SubElement(channel, "item")
        link = SITE + "/" + issue_path(issue)
        prefix = {'sample': '[样刊] ', 'curated': '[精选] '}.get(issue.get('status'), '')
        values = [("title", prefix + issue['title']), ("link", link), ("guid", link), ("description", issue.get('coverage', '') + " " + issue['intro'])]
        for key, value in values:
            ET.SubElement(item, key).text = value
        published = datetime.fromisoformat(issue['date'] + "T00:00:00+08:00").astimezone(timezone.utc)
        ET.SubElement(item, "pubDate").text = published.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)


def validate(issue, path):
    date.fromisoformat(issue['date'])
    slug = issue.get('slug', issue['date'])
    if not re.fullmatch(re.escape(issue['date']) + r'(?:-[a-z0-9]+)*', slug) or path.stem != slug:
        raise ValueError(f"Invalid issue slug or filename: {path.name}")
    for key in ['title', 'intro', 'coverage', 'stories']:
        if not issue.get(key):
            raise ValueError(f"Missing {key} in {path.name}")
    ids = set()
    for story in issue['stories']:
        for key in ['id', 'category', 'title', 'organization', 'summary', 'why', 'limitation', 'sources']:
            if not story.get(key):
                raise ValueError(f"Missing story {key} in {path.name}")
        if not re.fullmatch(r'[a-z0-9-]+', story['id']) or story['id'] in ids or story['id'] in ('technical-explainer', 'research-supplement'):
            raise ValueError(f"Invalid or repeated story ID in {path.name}")
        ids.add(story['id'])
        if story['category'] not in CATEGORIES:
            raise ValueError(f"Unknown category in {path.name}")
        if story.get('published'):
            date.fromisoformat(story['published'])
        for source in story['sources']:
            if not source.get('label'):
                raise ValueError(f"Missing source label in {path.name}")
            url(source['url'])
    for reading in issue.get('reading', []):
        url(reading['url'])
    featured = issue.get('featured_ids', [])
    if not isinstance(featured, list) or any(not isinstance(story_id, str) for story_id in featured):
        raise ValueError(f"Invalid featured story IDs in {path.name}")
    if len(featured) > 6 or len(featured) != len(set(featured)) or any(story_id not in ids for story_id in featured):
        raise ValueError(f"Invalid featured story IDs in {path.name}")
    for highlight in issue.get('highlights', []):
        if highlight.get('story_id') and highlight['story_id'] not in ids:
            raise ValueError(f"Invalid highlight story ID in {path.name}")
    if 'technical_explainer' in issue:
        validate_technical_explainer(issue['technical_explainer'], path.name)
    if 'research_supplement' in issue:
        validate_technical_explainer(issue['research_supplement'], f"{path.name} research_supplement")


def validate_technical_explainer(lesson, filename):
    def text(value, location):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid technical explainer {location} in {filename}")

    def text_list(value, location, required=True):
        if not isinstance(value, list) or (required and not value):
            raise ValueError(f"Invalid technical explainer {location} in {filename}")
        for item in value:
            text(item, location)

    if not isinstance(lesson, dict):
        raise ValueError(f"Invalid technical explainer in {filename}")
    if not isinstance(lesson.get('id'), str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', lesson['id']):
        raise ValueError(f"Invalid technical explainer ID in {filename}")
    for key in ['title', 'summary', 'why_now', 'takeaway']:
        text(lesson.get(key), key)
    minutes = lesson.get('reading_minutes')
    if type(minutes) is not int or not 1 <= minutes <= 30:
        raise ValueError(f"Technical explainer reading_minutes must be 1–30 in {filename}")
    if not isinstance(lesson.get('sections'), list) or not lesson['sections']:
        raise ValueError(f"Missing technical explainer sections in {filename}")
    for section in lesson['sections']:
        if not isinstance(section, dict):
            raise ValueError(f"Invalid technical explainer section in {filename}")
        text(section.get('heading'), 'section heading')
        text_list(section.get('paragraphs'), 'section paragraphs')
        if 'bullets' in section:
            text_list(section['bullets'], 'section bullets', required=False)
    if 'comparison' in lesson:
        comparison = lesson['comparison']
        if not isinstance(comparison, dict):
            raise ValueError(f"Invalid technical explainer comparison in {filename}")
        text(comparison.get('caption'), 'comparison caption')
        text_list(comparison.get('columns'), 'comparison columns')
        if len(comparison['columns']) < 2 or not isinstance(comparison.get('rows'), list) or not comparison['rows']:
            raise ValueError(f"Invalid technical explainer comparison dimensions in {filename}")
        for row in comparison['rows']:
            text_list(row, 'comparison row')
            if len(row) != len(comparison['columns']):
                raise ValueError(f"Technical explainer table column mismatch in {filename}")
    if 'example' in lesson:
        example = lesson['example']
        if not isinstance(example, dict):
            raise ValueError(f"Invalid technical explainer example in {filename}")
        text(example.get('title'), 'example title')
        text_list(example.get('paragraphs'), 'example paragraphs')
    text_list(lesson.get('checklist'), 'checklist')
    if not isinstance(lesson.get('sources'), list) or not lesson['sources']:
        raise ValueError(f"Missing technical explainer sources in {filename}")
    for source in lesson['sources']:
        if not isinstance(source, dict):
            raise ValueError(f"Invalid technical explainer source in {filename}")
        text(source.get('label'), 'source label')
        url(source.get('url'))


def validate_radar(radar):
    def require_text(value, location):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing or invalid {location} in radar.json")

    def text_list(value, location):
        if not isinstance(value, list):
            raise ValueError(f"Invalid {location} in radar.json")
        for item in value:
            require_text(item, location)

    def verification(value, location):
        if not isinstance(value, dict) or value.get('status', 'unverified') not in VERIFICATION_LABELS:
            raise ValueError(f"Invalid verification status for {location} in radar.json")
        if value.get('checked_on'):
            date.fromisoformat(value['checked_on'])
        if value.get('resolved_url'):
            url(value['resolved_url'])

    ids = set()

    def identifier(value, location):
        if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9-]+', value) or value in ids:
            raise ValueError(f"Invalid or repeated {location} ID in radar.json")
        ids.add(value)

    for key in ['title', 'intro']:
        require_text(radar.get(key), key)
    if radar.get('updated_on'):
        date.fromisoformat(radar['updated_on'])
    text_list(radar.get('selection_rules'), 'selection rules')
    if not isinstance(radar.get('groups'), list) or not radar['groups']:
        raise ValueError("Missing source groups in radar.json")
    for group in radar['groups']:
        if not isinstance(group, dict):
            raise ValueError("Invalid source group in radar.json")
        identifier(group.get('id'), 'group')
        for key in ['group', 'description']:
            require_text(group.get(key), f"group {key}")
        if not isinstance(group.get('sources'), list) or not group['sources']:
            raise ValueError(f"Missing sources in radar group {group['id']}")
        for source in group['sources']:
            if not isinstance(source, dict):
                raise ValueError(f"Invalid source in radar group {group['id']}")
            identifier(source.get('id'), 'source')
            for key in ['name', 'role']:
                require_text(source.get(key), f"source {key}")
            if source.get('url'):
                url(source['url'])
            verification(source.get('verification', {}), source['id'])
            for key in ['aliases', 'watch_terms']:
                text_list(source.get(key, []), f"source {source['id']} {key}")
            for key in ['channels', 'evidence']:
                if not isinstance(source.get(key, []), list):
                    raise ValueError(f"Invalid {key} for {source['id']} in radar.json")
                for item in source.get(key, []):
                    if not isinstance(item, dict):
                        raise ValueError(f"Invalid {key} item for {source['id']} in radar.json")
                    require_text(item.get('label'), f"{key} label")
                    url(item.get('url') or '')
                    if key == 'channels':
                        require_text(item.get('kind'), f"channel kind for {source['id']}")
                        verification(item, f"channel {source['id']}")
                    elif item.get('published'):
                        date.fromisoformat(item['published'])


def main():
    global BASE, SITE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-path', default='')
    parser.add_argument('--site-url', default='https://trimason.github.io/ai-daily')
    args = parser.parse_args()
    BASE = '/' + args.base_path.strip('/') if args.base_path.strip('/') else ''
    SITE = args.site_url.rstrip('/')
    if urlparse(SITE).scheme not in ('https', 'http'):
        parser.error('--site-url must use https:// or http://')
    issues = []
    for path in sorted((ROOT / 'content/issues').glob('*.json'), reverse=True):
        issue = json.loads(path.read_text(encoding='utf-8'))
        validate(issue, path)
        issues.append(issue)
    if not issues:
        parser.error('No content found in content/issues')
    status_rank = {'sample': 0, 'curated': 1, 'daily': 2}
    issues.sort(key=lambda i: (i['date'], status_rank.get(i.get('status'), 2), i.get('slug', i['date'])), reverse=True)
    radar = json.loads((ROOT / 'content/radar.json').read_text(encoding='utf-8'))
    validate_radar(radar)
    keywords = json.loads((ROOT / 'content/keywords.json').read_text(encoding='utf-8'))
    recent = json.loads((ROOT / 'content/recent-signals.json').read_text(encoding='utf-8'))
    output = ROOT / 'dist'
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    shutil.copytree(ROOT / 'assets', output / 'assets')
    pages = {'index.html': home(issues, keywords, recent), 'archive/index.html': archives(issues), 'topics/index.html': topics(issues), 'radar/index.html': research_radar(radar, keywords, recent), 'about/index.html': about()}
    pages.update({issue_path(i) + 'index.html': daily(i, issues) for i in issues})
    for path, content in pages.items():
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    (output / 'markdown').mkdir()
    for issue in issues:
        (output / 'markdown' / (issue.get('slug', issue['date']) + '.md')).write_text(markdown(issue), encoding='utf-8')
    (output / 'feed.xml').write_bytes(feed(issues))
    (output / '.nojekyll').touch()
    sitemap = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in pages:
        item = ET.SubElement(sitemap, 'url')
        ET.SubElement(item, 'loc').text = SITE + '/' + path.removesuffix('index.html')
    (output / 'sitemap.xml').write_bytes(ET.tostring(sitemap, encoding='utf-8', xml_declaration=True))
    print(f'Built {len(pages)} pages, {len(issues)} issues, {sum(len(i["stories"]) for i in issues)} stories → {output}')


if __name__ == '__main__':
    main()
