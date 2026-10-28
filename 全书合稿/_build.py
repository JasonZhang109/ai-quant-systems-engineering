#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《AI量化系统工程：研究、开发与验证》全书合稿构建脚本（可复现）

输入（只读）：../书稿/*.md   （26 个文本单元：序章 + 24 章 + 单一附录）
输出：
  AI量化系统工程_全书合稿_v1.0.md      成书正文（截断「编辑附记」）
  AI量化系统工程_全书合稿_v1.0.html    自包含阅读版（含可点击目录）
  AI量化系统工程_编辑附记汇编_v1.0.md  工作记录卷（26 份编辑附记）

约定：
1. 「编辑附记（不入书）」及其后内容不进成书，合稿时截断；另收入汇编卷。
2. 单元之间用 `---` 分隔。
3. 不改动 ../书稿/ 下任何源文件。
"""
import io, os, re, glob, html, datetime

SRC = '../书稿'
OUT_MD = 'AI量化系统工程_全书合稿_v1.0.md'
OUT_HTML = 'AI量化系统工程_全书合稿_v1.0.html'
OUT_NOTES = 'AI量化系统工程_编辑附记汇编_v1.0.md'
BOOK_TITLE = 'AI量化系统工程'
BOOK_SUB = '研究、开发与验证'
NOTES_MARK = '编辑附记（不入书）'
TOC_PLACEHOLDER = 'TOCPLACEHOLDERXYZ'


def unit_paths():
    """阅读顺序：序章 → 第01..24章 → 附录（单一附录）"""
    order = sorted(glob.glob(os.path.join(SRC, '序章*.md')))
    ch = {}
    for p in glob.glob(os.path.join(SRC, '第*章_*.md')):
        ch[int(re.search(r'第(\d+)章', os.path.basename(p)).group(1))] = p
    order += [ch[i] for i in sorted(ch)]
    order += sorted(glob.glob(os.path.join(SRC, '附录*.md')))
    return order


def split_unit(text):
    """返回 (正文, 附记全文)。附记全文自其标题行起；无附记时返回 (正文, '')。

    允许「已剥离附记」的源文件（公开发布版）：此时整个文件即正文。
    """
    i = text.find(NOTES_MARK)
    if i < 0:
        body = text.rstrip()
        body = re.sub(r'\n+---\s*$', '', body).rstrip()
        return body, ''
    cut = text.rfind('\n', 0, i)
    body = text[:cut].rstrip()
    body = re.sub(r'\n+---\s*$', '', body).rstrip()
    notes = text[cut:].lstrip('\n').rstrip() + '\n'
    return body, notes


def title_of(body):
    return re.match(r'^#\s+(.+)$', body, re.M).group(1).strip()


def unit_kind(title):
    if title.startswith('附录'):
        return 'appendix'
    if title.startswith('序章'):
        return 'preface'
    return 'chapter'


def build_md_toc(units):
    """Markdown 目录：纯文本（不依赖各渲染器的锚点规则）"""
    out = []
    for _p, body, _n in units:
        h1 = title_of(body)
        out.append(f'- **{h1}**')
        k = unit_kind(h1)
        if k == 'appendix':
            # 单一附录：二级节是 A–H 八个部分，三级节是各部分的 X.n
            pat = r'^(##|###)\s+(.+)$'
        else:
            pat = r'^##\s+(.+)$'
        for m in re.finditer(pat, body, re.M):
            t = (m.group(2) if k == 'appendix' else m.group(1)).strip()
            if t.startswith('编辑附记') or t == '阅读约定':
                continue
            if k == 'appendix' and m.group(1) == '###':
                out.append(f'    - {t}')
            else:
                out.append(f'  - {t}')
    return '\n'.join(out)


def build_html_toc(body_html):
    """从**渲染结果**读回 (level, id, 文本)，保证目录链接必然命中。"""
    hs = re.findall(r'<h([1-4]) id="([^"]+)">(.*?)</h\1>', body_html, re.S)
    items, kind = [], None
    for lvl, hid, inner in hs:
        text = html.unescape(re.sub(r'<[^>]+>', '', inner)).strip()
        if text.startswith('《'):          # 书名页，不入目录
            continue
        if lvl == '1':
            kind = unit_kind(text)
            items.append((kind, 1, hid, text))
        elif kind == 'appendix':
            # 单一附录：收二级节（A–H）与三级节（X.n），跳过「阅读约定」
            if lvl in ('2', '3') and not text.startswith('编辑附记') and text != '阅读约定':
                items.append((kind, int(lvl), hid, text))
        elif lvl == '2' and text != '目录' and not text.startswith('编辑附记'):
            items.append((kind, 2, hid, text))
    out, open_l1, open_l2 = [], False, False
    for kind, lvl, hid, text in items:
        a = f'<a href="#{hid}">{html.escape(text)}</a>'
        if lvl == 1:
            if open_l2:
                out.append('</ul></li>')
                open_l2 = False
            if open_l1:
                out.append('</ul></li>')
            out.append(f'<li>{a}<ul>')
            open_l1 = True
        elif kind == 'appendix' and lvl == 2:
            if open_l2:
                out.append('</ul></li>')
            out.append(f'<li>{a}<ul>')
            open_l2 = True
        else:
            out.append(f'<li>{a}</li>')
    if open_l2:
        out.append('</ul></li>')
    if open_l1:
        out.append('</ul></li>')
    return '<ul>' + ''.join(out) + '</ul>'


CSS = """
:root{--fg:#1a1a1a;--muted:#5b6470;--line:#e2e5ea;--bg:#fff;--soft:#f6f7f9;
 --accent:#1f5fa9;--side:#fafbfc;--hl:#eef4fc;--bar:255,255,255;}
:root[data-theme="dark"]{--fg:#dfe3e8;--muted:#96a0ac;--line:#2b323a;--bg:#151a1f;
 --soft:#1d242b;--accent:#6fa8e8;--side:#11161a;--hl:#22303f;--bar:21,26,31;}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;padding-left:19.5rem;background:var(--bg);color:var(--fg);
 font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
 font-size:16.5px;line-height:1.95;}

/* ---- 顶栏与进度 ---- */
#prog{position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent);z-index:60;transition:width .1s linear;}
.bar{position:fixed;top:0;left:0;right:0;height:3.1rem;display:flex;align-items:center;gap:.6rem;
 padding:0 1rem;background:rgba(var(--bar),.92);backdrop-filter:blur(8px);
 border-bottom:1px solid var(--line);z-index:50;}
.bar .brand{flex:1;font-size:.9rem;font-weight:600;color:var(--fg);text-decoration:none;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.bar button{border:1px solid var(--line);background:transparent;color:var(--fg);
 border-radius:6px;padding:.3rem .55rem;font-size:.85rem;cursor:pointer;line-height:1.2;}
.bar button:hover{background:var(--soft);}
#menu{display:none;}

/* ---- 侧栏目录 ---- */
.side{position:fixed;top:3.1rem;bottom:0;left:0;width:19.5rem;background:var(--side);
 border-right:1px solid var(--line);display:flex;flex-direction:column;z-index:40;}
.side .head{padding:.8rem 1rem .5rem;font-size:.78rem;letter-spacing:.08em;color:var(--muted);}
.side input{width:calc(100% - 2rem);margin:0 1rem .6rem;padding:.42rem .6rem;
 border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font-size:.85rem;}
.side input:focus{outline:2px solid var(--accent);outline-offset:-1px;}
.tocnav{flex:1;overflow-y:auto;padding:.2rem 1rem 2rem;font-size:.86rem;line-height:1.65;}
.tocnav ul{list-style:none;margin:0;padding-left:.85rem;}
.tocnav>ul{padding-left:0;}
.tocnav li{margin:.1rem 0;}
.tocnav a{display:block;padding:.12rem .35rem;border-radius:4px;color:var(--muted);text-decoration:none;}
.tocnav a:hover{background:var(--soft);color:var(--fg);}
.tocnav>ul>li>a{font-weight:600;color:var(--fg);margin-top:.25rem;}
.tocnav a.on{background:var(--hl);color:var(--accent);font-weight:600;}
.tocnav li.hide{display:none;}
.scrim{display:none;position:fixed;inset:3.1rem 0 0 0;background:rgba(0,0,0,.35);z-index:35;}

/* ---- 正文 ---- */
.wrap{max-width:46rem;margin:0 auto;padding:4.4rem 2.2rem 8rem;scroll-margin-top:4rem;}
h1,h2,h3,h4{line-height:1.45;font-weight:700;scroll-margin-top:3.9rem;}
h1{font-size:1.85rem;margin:3.4rem 0 1.2rem;padding-bottom:.5rem;border-bottom:2px solid var(--line);}
h2{font-size:1.35rem;margin:2.4rem 0 .9rem;}
h3{font-size:1.12rem;margin:1.9rem 0 .7rem;}
h4{font-size:1rem;margin:1.5rem 0 .6rem;}
p{margin:.85rem 0;}
a{color:var(--accent);text-decoration:none;}
a:hover{text-decoration:underline;}
hr{border:0;border-top:1px solid var(--line);margin:2.6rem 0;}
blockquote{margin:1.2rem 0;padding:.7rem 1.1rem;background:var(--soft);
 border-left:4px solid var(--accent);border-radius:0 4px 4px 0;}
blockquote p{margin:.4rem 0;}
code{background:var(--soft);padding:.12em .38em;border-radius:3px;
 font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;
 overflow-wrap:anywhere;}
pre{background:var(--soft);border:1px solid var(--line);border-radius:6px;
 padding:.9rem 1.1rem;overflow-x:auto;line-height:1.6;}
pre code{background:none;padding:0;font-size:.86rem;overflow-wrap:normal;}
table{border-collapse:collapse;width:100%;margin:1.1rem 0;font-size:.92rem;display:block;overflow-x:auto;}
th,td{border:1px solid var(--line);padding:.5rem .7rem;text-align:left;vertical-align:top;}
th{background:var(--soft);font-weight:600;}
tr:nth-child(even) td{background:rgba(127,127,127,.04);}
img{max-width:100%;height:auto;}

/* ---- 章节目录卡片 ---- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(13.5rem,1fr));gap:.6rem;margin:1.4rem 0 2.6rem;}
.grid a{display:flex;gap:.55rem;align-items:baseline;padding:.6rem .75rem;border:1px solid var(--line);
 border-radius:8px;color:var(--fg);text-decoration:none;background:var(--bg);}
.grid a:hover{background:var(--hl);border-color:var(--accent);text-decoration:none;}
.grid .num{font-size:.74rem;color:var(--accent);font-weight:700;white-space:nowrap;
 font-variant-numeric:tabular-nums;}
.grid .tt{font-size:.9rem;line-height:1.45;}

#back{position:fixed;right:1.1rem;bottom:1.1rem;background:var(--accent);color:#fff;
 width:2.4rem;height:2.4rem;line-height:2.3rem;text-align:center;border-radius:50%;
 font-size:1rem;box-shadow:0 2px 10px rgba(0,0,0,.2);opacity:0;pointer-events:none;
 transition:opacity .2s;z-index:45;text-decoration:none;}
#back.show{opacity:1;pointer-events:auto;}

@media (max-width:960px){
 body{padding-left:0;}
 .bar{display:flex;} #menu{display:inline-block;}
 .side{transform:translateX(-100%);transition:transform .22s ease;width:17.5rem;box-shadow:0 0 24px rgba(0,0,0,.18);}
 .side.open{transform:none;}
 .scrim.show{display:block;}
 .wrap{margin:0;padding:4.2rem 1.15rem 6rem;max-width:none;}
 h1{font-size:1.5rem;} h2{font-size:1.2rem;}
 body{font-size:16px;line-height:1.9;}
}
@media print{
 body{padding-left:0;}
 .bar,.side,.scrim,#back,#prog{display:none!important;}
 .wrap{margin:0;max-width:none;padding:0;}
 body{font-size:10.5pt;line-height:1.75;background:#fff;color:#000;}
 h1{page-break-before:always;font-size:16pt;}
 h1:first-of-type{page-break-before:avoid;}
 h2,h3{page-break-after:avoid;}
 pre,table,blockquote{page-break-inside:avoid;}
 .grid{display:none;}
}
"""


def main():
    paths = unit_paths()
    assert len(paths) == 26, f'单元数应为 26，实际 {len(paths)}'

    units, rows = [], []
    body_total = notes_total = 0
    for p in paths:
        raw = io.open(p, encoding='utf-8').read()
        body, notes = split_unit(raw)
        units.append((p, body, notes))
        body_total += len(body.encode('utf-8'))
        notes_total += len(notes.encode('utf-8'))
        rows.append((os.path.basename(p), title_of(body),
                     len(body.encode('utf-8')), len(notes.encode('utf-8'))))

    # 生成日期：默认取当天；设 BUILD_DATE=YYYY-MM-DD 可固定，便于逐字节复现
    stamp = os.environ.get('BUILD_DATE') or datetime.date.today().isoformat()

    # ---------------- 成书 Markdown ----------------
    # 公开版源文件已剥离附记、也不产出汇编卷，前言不得指向不存在的文件。
    if notes_total > 0:
        about = f"""> **关于本合稿的两点说明。**
>
> 第一，各单元原文件末尾的「**编辑附记（不入书）**」是写作与审校用的工作记录（章型声明、状态变更留痕、教学示例清单、待核验项、交叉引用账），按标记本身**不进入成书**，本合稿已将其截断。**这些记录并未丢弃**，已全文收入配套的《{BOOK_TITLE}_编辑附记汇编_v1.0.md》；正文中「见编辑附记」一类的指向，请到该汇编卷中查。本合稿因此比 {len(units)} 个单元的原文件合计**少 {notes_total:,} 字节**。
>
> 第二，全书统一使用 ASCII 双引号 `"` 作为中文引号；表格单元格内代码中的竖线一律写作 `\\|`。这两条是排版约定，不是内容差异。"""
    else:
        about = """> **关于本合稿的说明。**
>
> 全书统一使用 ASCII 双引号 `"` 作为中文引号；表格单元格内代码中的竖线一律写作 `\\|`。这两条是排版约定，不是内容差异。"""

    front = f"""# 《{BOOK_TITLE}：{BOOK_SUB}》

**全书合稿 v1.0** ｜ 生成日期 {stamp} ｜ 共 {len(units)} 个文本单元

{about}

---

## 目录

{build_md_toc(units)}

---
"""
    merged = front + '\n\n' + '\n\n---\n\n'.join(b for _p, b, _n in units) + '\n'
    io.open(OUT_MD, 'w', encoding='utf-8').write(merged)

    # ---------------- 编辑附记汇编 ----------------
    # 公开发布版的源文件已剥离附记，此时不产出汇编卷。
    if notes_total > 0:
        vol = [f"""# 《{BOOK_TITLE}》编辑附记汇编 v1.0

**生成日期 {stamp}** ｜ 共 {len(units)} 份 ｜ 合计 {notes_total:,} 字节

> 本卷收录 {len(units)} 个文本单元原文件末尾的「**编辑附记（不入书）**」，供写作、审校与统稿使用。**它不属于成书正文**——成书正文见《{BOOK_TITLE}_全书合稿_v1.0.md》。正文中「见编辑附记」一类的指向，指的就是本卷对应单元的内容。

---
"""]
        for p, body, notes in units:
            vol.append(f"# {title_of(body)}　·　编辑附记\n\n{notes}\n\n---\n")
        io.open(OUT_NOTES, 'w', encoding='utf-8').write('\n'.join(vol))

    # ---------------- HTML ----------------
    import markdown
    try:
        from markdown.extensions.toc import slugify_unicode as slug
    except Exception:
        slug = None
    cfg = {'toc': {'toc_depth': '1-3', 'anchorlink': False}}
    if slug:
        cfg['toc']['slugify'] = slug
    md = markdown.Markdown(
        extensions=['tables', 'fenced_code', 'toc', 'sane_lists', 'attr_list'],
        extension_configs=cfg)

    if notes_total > 0:
        html_about = (f'> 各单元末尾的「编辑附记（不入书）」不进入成书，已全文收入配套的'
                      f'《{BOOK_TITLE}_编辑附记汇编_v1.0.md》。'
                      f'全书统一使用 ASCII 双引号 `"` 作为中文引号。')
    else:
        html_about = '> 全书统一使用 ASCII 双引号 `"` 作为中文引号。'

    src = f"""# 《{BOOK_TITLE}：{BOOK_SUB}》

**全书合稿 v1.0** ｜ 生成日期 {stamp} ｜ 共 {len(units)} 个文本单元

{html_about}

---

## 目录

{TOC_PLACEHOLDER}

---

""" + '\n\n---\n\n'.join(b for _p, b, _n in units) + '\n'

    body_html = md.convert(src)
    toc = build_html_toc(body_html)
    ph = f'<p>{TOC_PLACEHOLDER}</p>'
    assert ph in body_html, '目录占位符未出现在渲染结果中'

    # 正文里的「目录」位置放章级卡片；细目全部交给左侧栏（避免 285 行重复两遍）
    h1s = [(hid, html.unescape(re.sub(r'<[^>]+>', '', inner)).strip())
           for lvl, hid, inner in re.findall(r'<h([1-4]) id="([^"]+)">(.*?)</h\1>', body_html, re.S)
           if lvl == '1']
    h1s = [(h, t) for h, t in h1s if not t.startswith('《')]
    assert len(h1s) == 26, f'章级标题应为 26，实际 {len(h1s)}'

    def card(hid, text):
        parts = text.split('\u3000')
        num, tt = (parts[0], parts[1]) if len(parts) > 1 else ('', text)
        return (f'<a href="#{hid}"><span class="num">{html.escape(num)}</span>'
                f'<span class="tt">{html.escape(tt)}</span></a>')

    body_html = body_html.replace(
        ph, '<div class="grid">' + ''.join(card(h, t) for h, t in h1s) + '</div>')

    # Mermaid → <pre class="mermaid">
    body_html = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        lambda m: '<pre class="mermaid">' + html.unescape(m.group(1)) + '</pre>',
        body_html, flags=re.S)

    toc_links = toc.count('<a href="#')

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>《{BOOK_TITLE}：{BOOK_SUB}》</title>
<meta name="description" content="《{BOOK_TITLE}：{BOOK_SUB}》全书，{len(h1s)} 个章级部分，单文件离线可读。">
<meta name="color-scheme" content="light dark">
<style>{CSS}</style>
</head>
<body>
<div id="prog"></div>
<header class="bar">
  <button id="menu" aria-label="打开目录">☰ 目录</button>
  <a class="brand" href="#top">《{BOOK_TITLE}》</a>
  <button id="theme" aria-label="切换深浅色">◐</button>
</header>
<aside class="side" id="toc">
  <div class="head">目录 · 共 {toc_links} 节</div>
  <input id="q" type="search" placeholder="筛选章节，如「回测」「第16章」" autocomplete="off">
  <nav class="tocnav">{toc}</nav>
</aside>
<div class="scrim" id="scrim"></div>
<main class="wrap" id="top">
{body_html}
</main>
<a id="back" href="#top" title="回到顶部" aria-label="回到顶部">↑</a>
<script>
(function(){{
  var root=document.documentElement,prog=document.getElementById('prog'),
      back=document.getElementById('back'),side=document.getElementById('toc'),
      scrim=document.getElementById('scrim'),menu=document.getElementById('menu'),
      q=document.getElementById('q'),
      links=[].slice.call(document.querySelectorAll('.tocnav a')),
      heads=[].slice.call(document.querySelectorAll('.wrap h1[id],.wrap h2[id]')),
      byId={{}},ticking=false;
  links.forEach(function(a){{var k=a.getAttribute('href').slice(1);if(!byId[k])byId[k]=a;}});

  var saved=null;
  try{{saved=localStorage.getItem('aq-theme');}}catch(e){{}}
  if(saved)root.setAttribute('data-theme',saved);
  else if(window.matchMedia&&matchMedia('(prefers-color-scheme:dark)').matches)
    root.setAttribute('data-theme','dark');
  document.getElementById('theme').addEventListener('click',function(){{
    var cur=root.getAttribute('data-theme')==='dark'?'light':'dark';
    root.setAttribute('data-theme',cur);
    try{{localStorage.setItem('aq-theme',cur);}}catch(e){{}}
  }});

  function close(){{side.classList.remove('open');scrim.classList.remove('show');}}
  menu.addEventListener('click',function(){{
    side.classList.toggle('open');scrim.classList.toggle('show');
  }});
  scrim.addEventListener('click',close);
  links.forEach(function(a){{
    a.addEventListener('click',function(){{if(innerWidth<=960)close();}});
  }});

  var lis=[].slice.call(document.querySelectorAll('.tocnav li'));
  q.addEventListener('input',function(){{
    var v=q.value.trim().toLowerCase();
    lis.forEach(function(li){{li.classList.remove('hide');}});
    if(!v)return;
    lis.forEach(function(li){{
      var own=li.querySelector('a'),kid=li.querySelector('ul');
      var hit=own&&own.textContent.toLowerCase().indexOf(v)>=0;
      if(!hit&&kid)hit=[].some.call(kid.querySelectorAll('a'),function(a){{
        return a.textContent.toLowerCase().indexOf(v)>=0;}});
      if(!hit)li.classList.add('hide');
    }});
  }});

  function onScroll(){{
    var h=document.documentElement.scrollHeight-innerHeight;
    prog.style.width=(h>0?(scrollY/h*100):0)+'%';
    back.classList.toggle('show',scrollY>700);
    var cur=null;
    for(var i=0;i<heads.length;i++){{
      if(heads[i].getBoundingClientRect().top<=132)cur=heads[i];else break;
    }}
    if(cur&&byId[cur.id]){{
      links.forEach(function(a){{a.classList.remove('on');}});
      byId[cur.id].classList.add('on');
    }}
    ticking=false;
  }}
  addEventListener('scroll',function(){{
    if(!ticking){{ticking=true;requestAnimationFrame(onScroll);}}
  }},{{passive:true}});
  onScroll();
}})();
</script>
<script type="module">
try {{
  const m = await import('https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs');
  m.default.initialize({{ startOnLoad: true, theme: 'neutral' }});
}} catch (e) {{
  document.querySelectorAll('pre.mermaid').forEach(function (el) {{
    el.insertAdjacentHTML('beforebegin',
      '<p style="color:#8a6d3b;font-size:.85rem">（图形需联网渲染；离线时下方为 Mermaid 源码）</p>');
  }});
}}
</script>
</body>
</html>
"""
    # 链接自检：在**整份文档**上做——侧栏目录也要纳入，否则检查会退化成空集
    ids = set(re.findall(r'\sid="([^"]+)"', doc))
    hrefs = set(re.findall(r'<a href="#([^"]+)"', doc))
    missing = sorted(hrefs - ids)
    assert not missing, f'目录存在悬空链接: {missing[:5]}'
    io.open(OUT_HTML, 'w', encoding='utf-8').write(doc)

    print(f'成书 MD  : {OUT_MD}  {len(merged.encode("utf-8")):,} B')
    print(f'阅读 HTML: {OUT_HTML}  {len(doc.encode("utf-8")):,} B')
    if notes_total > 0:
        print(f'附记汇编 : {OUT_NOTES}  {len(io.open(OUT_NOTES,encoding="utf-8").read().encode("utf-8")):,} B')
    else:
        print('附记汇编 : （源文件无附记，未生成）')
    print(f'正文 {body_total:,} B ｜ 附记 {notes_total:,} B ｜ 源文件合计 {body_total+notes_total:,} B')
    print(f'目录链接 {toc_links} 条，全部命中（0 悬空）')


if __name__ == '__main__':
    main()
