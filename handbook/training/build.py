#!/usr/bin/env python3
"""将培训 Markdown 与经过 Archify 验证的独立图打包为无外部依赖的离线 HTML。

只处理本手册使用的 Markdown 子集。图的原始 HTML 保持不变，以 srcdoc 嵌入。
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / '06-团队培训使用手册.md'
DIAGRAMS = {
    'baseline-map': '基线与业务项目架构',
    'delivery-flow': '需求到交付流程',
    'quality-gates': '质量门禁流程',
}

def inline(text: str) -> str:
    tokens: list[str] = []
    def hold(value: str) -> str:
        tokens.append(value)
        return f'\x00{len(tokens)-1}\x00'
    text = re.sub(r'`([^`]+)`', lambda m: hold('<code>'+html.escape(m[1])+'</code>'), text)
    def link(m: re.Match) -> str:
        url = m[2]
        if url.endswith('.md') and '/' not in url:
            url = '../' + url
        if url == 'training/index.html':
            url = 'index.html'
        if url.startswith(('javascript:', 'data:')):
            raise ValueError('不允许的链接协议')
        return hold(f'<a href="{html.escape(url, quote=True)}">{html.escape(m[1])}</a>')
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'\x00(\d+)\x00', lambda m: tokens[int(m[1])], text)

def diagram(slug: str) -> str:
    title = DIAGRAMS[slug]
    path = HERE / 'assets' / slug / f'{slug}.html'
    blob = path.read_bytes()
    receipt = json.loads(path.with_suffix('.finalize-summary.json').read_text())
    assert receipt['ok'] and all(value == 'pass' for value in receipt['gates'].values()), slug
    assert receipt['artifact']['sha256'] == hashlib.sha256(blob).hexdigest(), slug
    return (f'<figure class="diagram"><figcaption>{title} <button type="button" data-open="{slug}">单独打开图</button></figcaption>'
            f'<iframe title="{title}" data-diagram="{slug}" loading="lazy" srcdoc="{html.escape(blob.decode(), quote=True)}"></iframe>'
            '</figure>')

def render(source: str) -> tuple[str, list[tuple[str, str]]]:
    lines=source.splitlines();result=[];toc=[];i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):
                code.append(lines[i]);i+=1
            result.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>');i+=1;continue
        m=re.fullmatch(r'<!-- diagram:([a-z-]+) -->',line)
        if m:result.append(diagram(m[1]));i+=1;continue
        m=re.match(r'^(#{1,3}) (.+)',line)
        if m:
            level=len(m[1]);anchor=f'section-{len(result)}'
            result.append(f'<h{level} id="{anchor}">{inline(m[2])}</h{level}>')
            if level==2:toc.append((anchor,m[2]))
            i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                row=lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*',c) for c in row):rows.append(row)
                i+=1
            result.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+inline(c.strip())+'</th>' for c in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in row)+'</tr>' for row in rows[1:])+'</tbody></table></div>');continue
        if line.startswith('> '):
            quote=[]
            while i<len(lines) and lines[i].startswith('> '):quote.append(inline(lines[i][2:]));i+=1
            result.append('<aside class="note">'+'<br>'.join(quote)+'</aside>');continue
        if re.match(r'^(?:- |\d+\. )',line):
            ordered=bool(re.match(r'^\d+\.',line));tag='ol' if ordered else 'ul';rows=[]
            pattern=r'^\d+\. (.+)' if ordered else r'^- (.+)'
            while i<len(lines) and (m:=re.match(pattern,lines[i])):
                value=m[1]
                if value.startswith('[ ] '):value='☐ '+value[4:]
                rows.append('<li>'+inline(value)+'</li>');i+=1
            result.append(f'<{tag}>'+''.join(rows)+f'</{tag}>');continue
        p=[]
        while i<len(lines) and lines[i].strip() and not re.match(r'^(?:#|```|\||>|<!--|- |\d+\. )',lines[i]):
            p.append(lines[i]);i+=1
        if not p:raise ValueError(f'未识别的 Markdown：{lines[i]}')
        result.append('<p>'+inline('\n'.join(p))+'</p>')
    return '\n'.join(result),toc

CSS='''
:root{color-scheme:light;--paper:#f7f6f1;--ink:#202d35;--muted:#5d6c72;--line:#d8dfdc;--accent:#116958}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:35px}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.85 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}a{color:var(--accent);text-underline-offset:4px}header{padding:38px 5vw 28px;border-bottom:1px solid var(--line);background:#eaf0e9}.eyebrow{font:12px/1.6 ui-monospace,monospace;letter-spacing:2px;color:var(--accent)}header p{margin:10px 0 0;font-size:19px}header button{float:right}button{font:inherit;font-size:13px;border:1px solid #bccbc2;border-radius:6px;background:white;color:var(--ink);padding:6px 12px;cursor:pointer}button:hover{background:#e3eee8}button:focus-visible,a:focus-visible{outline:3px solid #cf812b;outline-offset:4px}.layout{max-width:1540px;margin:auto;display:grid;grid-template-columns:235px minmax(0,1fr);gap:40px;padding:40px 4vw}nav{position:sticky;top:28px;align-self:start;font-size:13px;max-height:90vh;overflow:auto}nav strong{display:block;margin-bottom:14px}nav a{display:block;padding:7px 0;color:var(--muted);text-decoration:none;border-bottom:1px solid #e0e4de}nav a:hover{color:var(--accent)}main{min-width:0;max-width:1080px}h1{font-size:34px;line-height:1.4;letter-spacing:-.8px;margin:0 0 24px}h2{font-size:25px;line-height:1.5;border-top:2px solid var(--accent);padding-top:23px;margin:64px 0 24px}h3{font-size:19px;margin:32px 0 14px}p{margin:16px 0}li{margin:8px 0}strong{font-weight:650}.note{border-left:4px solid var(--accent);background:#edf1e8;padding:18px 22px;color:#44554c;font-size:14px}code{font:13px/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere;background:#e8ece6;padding:2px 5px;border-radius:3px}pre{background:#192c31;color:#e4eee6;border-radius:8px;padding:20px;overflow:auto}pre code{color:inherit;background:none;padding:0;white-space:pre;font-size:13px;overflow-wrap:normal}.table-wrap{overflow-x:auto;margin:22px 0}table{border-collapse:collapse;width:100%;font-size:14px}th{text-align:left;background:#e8eee7;color:#254b42}th,td{padding:12px 14px;border:1px solid var(--line);vertical-align:top}td{min-width:100px}tbody tr:nth-child(even){background:#fbfcf8}.diagram{margin:30px 0;border:1px solid var(--line);border-radius:10px;background:#fff}figcaption{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 18px;font-size:14px;font-weight:600;border-bottom:1px solid var(--line)}iframe{border:0;width:100%;height:800px;display:block;border-radius:0 0 10px 10px}footer{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding:25px 5vw}.diagram-static{display:none}@media(min-width:1700px){.layout{gap:60px}}@media(max-width:1050px){.layout{display:block;padding:25px 5vw}nav{position:static;max-height:none;columns:2;margin-bottom:35px}nav strong{column-span:all}h1{font-size:28px}iframe{height:780px}header p{font-size:16px}}@media(max-width:600px){nav{columns:1}h1{font-size:24px}h2{font-size:22px}th,td{padding:9px;font-size:13px}iframe{height:740px}figcaption{align-items:flex-start}header button{float:none;margin-top:15px}pre{padding:14px}}@media print{body{background:white;font-size:11pt}header,nav,button{display:none}.layout{display:block;padding:0;max-width:none}main{max-width:none}h1{font-size:24pt}h2{break-before:page;font-size:19pt;margin-top:0}h3{break-after:avoid}pre{white-space:pre-wrap;background:#f2f4f2;color:black;overflow:visible}pre code{white-space:pre-wrap}table{font-size:9pt}tr{break-inside:avoid}iframe{display:none}.diagram-static{display:block;width:100%;height:auto}figcaption{font-size:11pt}.table-wrap{overflow:visible}.note{background:#f4f5f0}a{color:inherit}footer{display:none}}
'''
JS=r'''
for(const button of document.querySelectorAll('[data-open]'))button.addEventListener('click',()=>{const frame=document.querySelector('iframe[data-diagram="'+button.dataset.open+'"]');const blob=new Blob([frame.srcdoc],{type:'text/html;charset=utf-8'});const url=URL.createObjectURL(blob);window.open(url,'_blank','noopener');setTimeout(()=>URL.revokeObjectURL(url),60000)});

'''

def main() -> None:
    body,toc=render(SOURCE.read_text())
    navigation=''.join(f'<a href="#{anchor}">{html.escape(label)}</a>' for anchor,label in toc)
    output=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AI 协作工程基线 · 团队培训使用手册</title><style>{CSS}</style></head><body><header><div class="eyebrow">AI-NATIVE ENGINEERING / TEAM HANDBOOK</div><p>从需求入库，到客户现场交付</p></header><div class="layout"><nav aria-label="章节目录"><strong>培训目录 · 2026.10</strong>{navigation}</nav><main>{body}</main></div><footer>依据 2026-10-23 仓库规范与脚本整理。示例不代表真实需求确认；自动检查与人工复核各自承担明确职责。</footer><script>{JS}</script></body></html>'''
    (HERE/'index.html').write_text(output)
    print(f'已生成 {HERE / "index.html"}，{len(toc)} 个章节，{len(DIAGRAMS)} 张交互图。')

if __name__=='__main__':main()
