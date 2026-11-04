"""Build offline, prose-first readers from reviewed content and PDF assets."""
from pathlib import Path
import base64
import hashlib
import html
import json

ROOT = None
SCRIPTS = Path(__file__).resolve().parent
assets, sources, cases = {}, {}, []
esc = lambda s: html.escape(str(s), quote=True)


def data_uri(path):
    import mimetypes
    return 'data:'+(mimetypes.guess_type(str(path))[0] or 'image/jpeg')+';base64,' + base64.b64encode((ROOT / path).read_bytes()).decode('ascii')


def location(asset):
    part = 'SI' if asset['source'].endswith('-si') else '正文'
    return asset.get('locator') or f'{part} · PDF第{asset["page"]}页'


def scientific_flow(case):
    nodes = {n['id']: n for n in case['nodes']}
    parts = [f'<svg class="flow" viewBox="0 0 340 {case.get("flow_height",540)}" role="group" aria-labelledby="flow-title"><title id="flow-title">{esc(case["short"])}的问题与证据路线</title>',
             '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#97adc5"/></marker></defs>']
    for edge in case['edges']:
        a, b = nodes[edge['from']], nodes[edge['to']]
        if a['y'] == b['y']:
            left_to_right = b['x'] > a['x']
            x1, x2 = (a['x']+160, b['x']) if left_to_right else (a['x'], b['x']+160)
            y1 = y2 = a['y']+34
            d = f'M{x1} {y1} L{x2} {y2}'
            label = ''
        else:
            x1, y1 = a['x']+80, a['y']+68
            x2, y2 = b['x']+80, b['y']
            # Long branch edges follow the open side of the diagram, never run through cards.
            if y2-y1 > 150:
                side = 8 if x1 < 170 else 332
                d = f'M{x1} {y1} C{x1} {y1+14} {side} {y1+14} {side} {y1+32} L{side} {y2-24} Q{side} {y2-10} {x2} {y2-10} L{x2} {y2}'
                label = ''
            else:
                mid = (y1+y2)/2
                d = f'M{x1} {y1} C{x1} {mid} {x2} {mid} {x2} {y2}'
                label = f'<text class="edge-label" x="{(x1+x2)/2}" y="{mid-4}">{esc(edge["label"])}</text>'
        kind = ' interpretation' if edge.get('kind') == 'interpretation' else ''
        parts.append(f'<path class="flow-edge{kind}" d="{d}" marker-end="url(#arrow)"><title>{esc(edge["label"])}</title></path>{label}')
    for n in case['nodes']:
        x, y = n['x'], n['y']
        name = ''.join(n['lines'])
        role = n['role']
        if n.get('figure_note'):
            role += ' · '+n['figure_note']
        elif not case.get('story_first') and not case.get('panel_reading'):
            section = next((s for s in case['sections'] if n['target'].startswith(s['id']+'-')),None)
            first_fig = next((b['figure'] for b in section['blocks'] if isinstance(b,dict) and 'figure' in b),None) if section else None
            if first_fig: role += ' · '+case['figures'][first_fig]['label']
        section_id = next((s['id'] for s in case['sections'] if n['target'].startswith(s['id']+'-')),'')
        parts.append(f'<a class="flow-node relation-node scientific-node" data-story-section="{esc(section_id)}" data-finding="{esc(n.get("finding",""))}" href="#{esc(n["target"])}" aria-label="{esc(name)}"><title>{esc(n.get("finding",name))}</title><rect x="{x}" y="{y}" width="160" height="68" rx="7"/><text class="node-role" x="{x+80}" y="{y+15}">{esc(role)}</text>')
        for i, line in enumerate(n['lines']):
            parts.append(f'<text x="{x+80}" y="{y+35+i*20}">{esc(line)}</text>')
        parts.append('</a>')
    parts.append('</svg>')
    return ''.join(parts)


def research_map_panel(case):
    nodes={n['id']:n for n in case['nodes']}
    if not nodes:
        reason=esc(case.get('omit_research_graph_reason','尚未提供论证关系。'))
        return '<details class="scientific-map" id="scientific-map"><summary>研究论证关系</summary><p>'+reason+'</p></details>'
    relationships=''.join('<li>'+esc(''.join(nodes[e['from']]['lines']))+' → <b>'+esc(e['label'])+'</b> → '+esc(''.join(nodes[e['to']]['lines']))+'</li>' for e in case['edges'])
    return '<details class="scientific-map" id="scientific-map"><summary>研究论证关系</summary><p>看证据怎样支撑判断；上方脑图用于阅读定位。点击论证节点可回到正文。</p>'+scientific_flow(case)+'<details class="relation-key"><summary>逐条看论证关系</summary><ul>'+relationships+'</ul></details></details>'


def figure_html(case, fid):
    f, a = case['figures'][fid], assets[fid]
    si = ' si' if a['source'].endswith('-si') else ''
    whole = f'<button data-open-figure="{fid}" data-mode="whole">查看完整复合图</button>' if f.get('parent') else ''
    display = ' compact-evidence' if f.get('display')=='compact' else ''
    return f'''<figure class="figure{si}{display}" id="figure-{fid}" tabindex="-1">
<button class="figure-image" data-open-figure="{fid}" aria-label="放大{esc(f['label'])}：{esc(f['title'])}"><img src="{data_uri(a['image'])}" alt="{esc(f['label']+'，'+f['title'])}" width="{a['width']}" height="{a['height']}" loading="lazy" decoding="async"></button>
<figcaption><span class="figure-label">{esc(f['label'])} · {esc(f['role'])}</span><h3 class="figure-title">{esc(f['title'])}</h3><p class="figure-caption">{esc(f['caption'])}</p>
<div class="figure-actions"><button data-open-figure="{fid}">放大原图</button>{whole}<button data-open-figure="{fid}" data-mode="page">{esc(a.get('full_view_label','查看完整原页'))}</button><span class="source-loc">{esc(location(a))}</span></div></figcaption></figure>'''


def render(case):
    case_id = case['id']
    paragraphs, used, article, md = set(), [], [], [f'# {case["title"]}', '', case['thesis'], '', f'{case["paper_title"]}  ', case['citation'], f'https://doi.org/{case["doi"]}', '', case['audience'], '']
    walk_steps = []
    figure_entries = []
    question_branches = []
    reading_layer = '主线'
    branch_side_counter = 0

    def fig(fid):
        assert fid not in used, ('duplicate figure', fid)
        assert assets[fid]['source'] in case['source_ids']
        if sources[assets[fid]['source']].get('format','pdf')=='pdf':
            assert 1 <= assets[fid]['page'] <= sources[assets[fid]['source']]['pages']
        used.append(fid)
        figure_entries.append({'id':fid,'section':sec['id'],'target':'figure-'+fid,'title':case['figures'][fid]['title'],'number':len(figure_entries)+1,'layer':reading_layer})
        f, a = case['figures'][fid], assets[fid]
        md.extend([f'![{f["label"]}：{f["title"]}]({a["image"]})', '', f'{f["caption"]}（{location(a)}）', ''])
        return figure_html(case, fid)

    def walk(w, section_id):
        step_id = w['id']
        fid = w['figure']
        f = case['figures'][fid]
        walk_steps.append({**w,'section':section_id,'number':len(walk_steps)+1})
        number = len(walk_steps)
        pid = step_id+'-lead'
        assert pid not in paragraphs
        paragraphs.add(pid)
        md.extend([f'### 局部补读 · {f["label"]}：{w["title"]}', '', f'<a id="{pid}"></a>', w['lead'], ''])
        fragment = fig(fid)
        figure_entries[-1].update(target=pid,title=w['title'],layer=reading_layer)
        label = '局部读法' if case.get('story_first') else f'读图 {number:02d}'
        output = [f'<div class="panel-step" id="step-{esc(step_id)}" data-panel="{esc(f["label"])}"><h3 class="step-heading"><span class="step-number">{label}</span><span><span class="panel-name">{esc(f["label"])}</span>{esc(w["title"])}</span></h3><p class="prose panel-lead" id="{pid}" tabindex="-1">{esc(w["lead"])}</p>',fragment]
        for i,p in enumerate(w['paragraphs'],1):
            body_id = f'{step_id}-explain-{i}'
            paragraphs.add(body_id)
            output.append(f'<p class="prose" id="{body_id}" tabindex="-1">{esc(p)}</p>')
            md.extend([p,''])
        output.append('</div>')
        return ''.join(output)

    for section_number, sec in enumerate(case['sections'],1):
        article.append(f'<section class="article-section story-trunk" id="{sec["id"]}" data-graph-node="{sec["id"]}" data-story-section="{sec["id"]}" aria-labelledby="heading-{sec["id"]}" tabindex="-1"><span class="trunk-stage-marker" aria-hidden="true">{section_number:02d}</span><h2 id="heading-{sec["id"]}">{esc(sec["title"])}</h2>')
        md.extend([f'<a id="{sec["id"]}"></a>',f'## {sec["title"]}', ''])
        if sec.get('reading_order'):
            article.append(f'<p class="reading-order">本段读图顺序：{esc(sec["reading_order"])}</p>')
            md.extend(['本段读图顺序：'+sec['reading_order'],''])
        count = 0
        detail_count = 0
        side_counts = {'left':0,'right':0}
        last_main_id = sec['id']
        branch_group = []
        junction_number = 0
        def flush_branch_group():
            nonlocal branch_group,junction_number
            if not branch_group:return
            junction_number += 1
            junction_id=f'junction-{sec["id"]}-{junction_number}'
            left=''.join(markup for side,markup,_,_ in branch_group if side=='left')
            right=''.join(markup for side,markup,_,_ in branch_group if side=='right')
            def entrances(side):
                return ''.join(f'<a class="branch-entry" data-open-branch="{bid}" data-side="{side}" href="#{bid}"><span class="entry-direction">{esc(next(b["code"] for b in question_branches if b["id"]==bid))} · {"↖ 左侧枝" if side=="left" else "右侧枝 ↗"}</span><span>{esc(title)}</span></a>' for s,_,bid,title in branch_group if s==side)
            article.append(f'<div class="branch-junction" id="{junction_id}" data-story-section="{sec["id"]}" data-origin="{esc(last_main_id)}"><div class="junction-entries"><div class="entry-lane entry-left">{entrances("left")}</div><span class="junction-dot" aria-hidden="true"></span><div class="entry-lane entry-right">{entrances("right")}</div></div><div class="branch-lane lane-left">{left}</div><div class="branch-lane lane-right">{right}</div></div>')
            branch_group=[]
        for block in sec['blocks']:
            if not (isinstance(block,dict) and 'detail' in block):flush_branch_group()
            if isinstance(block, str):
                count += 1
                pid = f'{sec["id"]}-p{count}'
                assert pid not in paragraphs
                paragraphs.add(pid)
                last_main_id = pid
                article.append(f'<p class="prose" id="{pid}" tabindex="-1">{esc(block)}</p>')
                md.extend([f'<a id="{pid}"></a>', block, ''])
            elif 'figure' in block:
                article.append(fig(block['figure']))
            elif 'figure_row' in block:
                article.append(f'<div class="figure-row" style="--figure-columns:{len(block["figure_row"])}" aria-label="同一论证中的图证比较">'+''.join(fig(fid) for fid in block['figure_row'])+'</div>')
            elif 'walkthrough' in block:
                article.append(walk(block['walkthrough'],sec['id']))
            else:
                detail = block['detail']
                detail_count += 1
                branch_id = f'branch-{sec["id"]}-{detail_count}'
                first_step = next((b['walkthrough'] for b in detail.get('blocks',[]) if 'walkthrough' in b),None)
                branch_target = first_step['id']+'-lead' if first_step else branch_id
                evidence_ids = [b['walkthrough']['figure'] for b in detail.get('blocks',[]) if 'walkthrough' in b]
                if detail.get('figure'):evidence_ids.append(detail['figure'])
                evidence_ids.extend(detail.get('figures',[]))
                detail_class = 'local-reading' if detail.get('kind')=='figure-reading' else 'supplement'
                side=detail.get('side') or ('left' if branch_side_counter%2==0 else 'right')
                side_counts[side] += 1
                code=f'{section_number:02d}·{"左" if side=="left" else "右"}{side_counts[side]}'
                question_branches.append({'id':branch_id,'section':sec['id'],'target':branch_id,'detail_target':branch_target,'title':detail['title'],'evidence':'、'.join(dict.fromkeys(case['figures'][fid]['label'] for fid in evidence_ids)),'side':side,'code':code,'origin':last_main_id,'kind':'si' if detail_class=='supplement' else 'explanation'})
                branch_side_counter += 1
                detail_start=len(article)
                article.append(f'<section class="{detail_class} story-detail branch-{side}" id="{branch_id}" data-graph-node="{branch_id}" data-graph-code="{esc(code)}" data-side="{side}" data-branch-id="{branch_id}" data-story-section="{sec["id"]}" tabindex="-1"><h3 class="branch-heading"><small class="leaf-kind"><span class="graph-code">{esc(code)}</span> · {"SI证据" if detail_class=="supplement" else "深入理解"}</small><span class="branch-title">{esc(detail["title"])}</span></h3>')
                reading_layer = '补读'
                md.extend([f'<a id="{branch_id}"></a>','<details>',f'<summary>{esc(code)} · {esc(detail["title"])}</summary>',''])
                for p in detail.get('paragraphs',[]):
                    article.append(f'<p>{esc(p)}</p>')
                    md.extend([p, ''])
                if detail.get('figure'):
                    article.append(fig(detail['figure']))
                for fid in detail.get('figures',[]):article.append(fig(fid))
                for inner in detail.get('blocks',[]):
                    article.append(walk(inner['walkthrough'],sec['id']))
                article.append(f'<a class="return-trunk" data-story-section="{sec["id"]}" href="#{esc(last_main_id)}">沿连线移回主干 ↑</a></section>')
                reading_layer = '主线'
                md.extend(['</details>',''])
                branch_group.append((side,''.join(article[detail_start:]),branch_id,detail['title']))
                del article[detail_start:]
        flush_branch_group()
        refs = '；'.join(sec['refs'])
        article.append(f'<p class="reading-ref">回读依据：{esc(refs)}</p></section>')
        md.extend([f'回读依据：{refs}', ''])
    assert set(used) == set(case['figures']), ('unused figures', set(case['figures'])-set(used))
    for n in case['nodes']:
        assert n['target'] in paragraphs, ('missing paragraph', n)
    node_ids = {n['id'] for n in case['nodes']}
    assert len(node_ids) == len(case['nodes'])
    for e in case['edges']:
        assert e['from'] in node_ids and e['to'] in node_ids
    graph_nodes=[]
    for index,sec in enumerate(case['sections'],1):
        original=next((n for n in case['nodes'] if n['target'].startswith(sec['id']+'-')),None)
        figure_labels=list(dict.fromkeys(case['figures'][f['id']]['label'] for f in figure_entries if f['section']==sec['id'] and f['layer']=='主线'))
        graph_nodes.append({'id':sec['id'],'type':'main','section':sec['id'],'target':sec['id'],'title':sec['title'],'code':f'{index:02d}','figures':'、'.join(figure_labels),'finding':original.get('finding','') if original else ''})
    graph_nodes.extend({'id':b['id'],'type':'branch','section':b['section'],'target':b['target'],'title':b['title'],'code':b['code'],'figures':b['evidence'],'side':b['side'],'origin':b['origin'],'kind':b['kind']} for b in question_branches)
    main_nodes=[n for n in graph_nodes if n['type']=='main']
    graph_edges=[{'from':a['id'],'to':b['id'],'kind':'reading-order','label':'接着读'} for a,b in zip(main_nodes,main_nodes[1:])]
    graph_edges.extend({'from':b['section'],'to':b['id'],'origin':b['origin'],'kind':'branch','label':'SI补证' if b['kind']=='si' else '就近细讲'} for b in question_branches)
    assert len({n['id'] for n in graph_nodes})==len(graph_nodes)
    assert all(n['target'] in ({s['id'] for s in case['sections']}|paragraphs|{b['id'] for b in question_branches}) for n in graph_nodes)
    config = {'figures': {}, 'pages': {}, 'composites': {},'researchGraph':{'nodes':case['nodes'],'edges':case['edges']},'readingGraph':{'nodes':graph_nodes,'edges':graph_edges}}
    identity={'id':case['id'],'title':case['title'],'sections':case['sections'],'figures':case['figures'],'sources':{sid:sources[sid]['sha256'] for sid in case['source_ids']}}
    config['readerIdentity']=hashlib.sha256(json.dumps(identity,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()[:24]
    (ROOT/'graphs').mkdir(exist_ok=True)
    (ROOT/'graphs'/f'{case_id}.reading-graph.json').write_text(json.dumps(config['readingGraph'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'graphs'/f'{case_id}.research-graph.json').write_text(json.dumps(config['researchGraph'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for fid in used:
        a, f = assets[fid], case['figures'][fid]
        page_key = f'{a["source"]}-{a["page"]}'
        config['figures'][fid] = {**f, 'location': location(a), 'page_key': page_key, 'full_view_label': a.get('full_view_label','查看完整原页'), 'full_view_description': a.get('full_view_description','完整PDF页面')}
        if page_key not in config['pages']:
            config['pages'][page_key] = data_uri(a['page_image'])
        if f.get('parent'):
            parent = f['parent']
            assert assets[parent]['source']==a['source'] and assets[parent]['page']==a['page']
            config['composites'][parent]={**case['composites'][parent],'image':data_uri(assets[parent]['image'])}
    panel_outline = ''
    if used:
        outline_steps = [{**w,'fid':w['id']} for w in figure_entries]
        groups = []
        for sec in case['sections']:
            steps = [w for w in outline_steps if w['section']==sec['id']]
            if not steps: continue
            links = ''.join(f'<li><a class="outline-link" data-story-section="{esc(sec["id"])}" href="#{esc(w["target"])}"><span class="outline-number">{esc(w["layer"])}</span><span><b>{esc(case["figures"][w["fid"]]["label"])}</b><small>{esc(w["title"])}</small></span></a></li>' for w in steps)
            groups.append(f'<details class="panel-group"><summary>{esc(sec["title"])}</summary><ol>{links}</ol></details>')
        outline_title = '图证索引 · 按文章脉络'
        hint = '需要核对图证时，再展开相应问题下的主线图或局部补读。'
        panel_outline = f'<details class="panel-outline route-card" id="panel-nav"><summary>{outline_title}</summary><p>{hint}</p><nav aria-label="按研究问题组织的图证索引">{"".join(groups)}</nav></details>'
    route_open = ' open'
    route_summary = '文章脉络脑图'
    encoded = json.dumps(config, ensure_ascii=False, separators=(',', ':')).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    tabs = ''.join(f'<a href="{esc(c.get("href",c["id"]+".html"))}"'+(' aria-current="page"' if c['id']==case_id else '')+f'>{esc(c["short"])}</a>' for c in cases)
    source_list = ''.join('<li>'+esc(sources[sid].get('description') or '原始来源')+' · <a href="'+esc(sources[sid]['local_href'])+'">打开本地原件</a></li>' for sid in case['source_ids'])
    draft_notice = ('<p class="paper-tip" role="status">'+esc(case["draft_notice"])+'</p>') if case.get("draft_notice") else ""
    if case.get("draft_notice"):md[0:0]=[case["draft_notice"], ""]
    doc = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(case['title'])} · PaperStory</title><style>{(SCRIPTS/'reader.css').read_text(encoding='utf-8')}</style></head><body class="paper-reader">
<a class="skip" href="#reading">跳到导读正文</a>
<header class="topbar"><a class="brand" href="{esc(case.get('home_href','index.html'))}">PaperStory<small>材料与化学 · 离线伴读</small></a><nav class="case-tabs" aria-label="切换样品">{tabs}</nav></header>
<main class="layout"><aside class="sidebar" aria-label="论文问题导航"><details class="route-card" id="route"{route_open}><summary>{route_summary}<small id="route-current"></small></summary><p>与主视图使用相同标题和编号；点击节点，镜头移到对应位置。</p><p class="current-location" id="current-location" aria-live="polite">正在读：文章开头</p><div class="map-actions"><button id="map-expand-all" aria-pressed="false">展开全部侧枝</button><span>当前阶段自动展开</span></div><div class="flow-wrap"><svg class="flow reading-map" id="reading-map" role="group" aria-label="与主画布一致的阅读脉络"></svg><nav class="map-fallback">{''.join(f'<a href="#{esc(n["target"])}">{esc(n["code"])} · {esc(n["title"])}</a>' for n in graph_nodes)}</nav></div><p class="current-finding" id="current-finding" hidden></p><div class="route-foot">竖向：阅读顺序　左右：对应细讲<a href="#reading">镜头移回文章开头 ↑</a></div><details class="paper-overview" id="paper-overview"><summary>画布位置 · 可点击移动</summary><svg id="paper-mini-map" role="group" aria-label="实际纸面位置与当前镜头范围"></svg><p>边框表示当前视窗；点击内容块可移近阅读。</p></details>{research_map_panel(case)}</details>{panel_outline}<p id="reader-status" class="sr-only" role="status" aria-live="polite"></p></aside>
<article class="reading" id="reading" tabindex="-1"><nav class="paper-tools" aria-label="画布镜头"><button id="paper-return" disabled>← 移回主干</button><span id="paper-position">主干 · 同一张纸</span><span class="paper-tool-gap"></span><button id="paper-context">看分叉关系</button><button id="paper-fit" title="将整张纸放入当前视窗">整张纸</button><button id="paper-wheel-mode" aria-pressed="false" title="切换普通滚轮的用途；Ctrl加滚轮始终缩放">滚轮：阅读</button><div class="paper-zoom" role="group" aria-label="缩放整张纸"><button id="paper-minus" aria-label="缩小整张纸">−</button><input id="paper-zoom-slider" type="range" min="0" max="1000" step="1" aria-label="整张纸缩放比例"><button id="paper-scale" aria-label="恢复100%阅读大小" title="恢复100%阅读大小">100%</button><button id="paper-plus" aria-label="放大整张纸">＋</button></div></nav><div class="paper-viewport" id="paper-viewport" tabindex="0" aria-label="论文阅读画布，空白直接拖动，文字可选，滚轮阅读，空格加拖拽任意位置，Ctrl加滚轮缩放"><div class="paper-world" id="paper-world"><svg class="paper-connections" aria-hidden="true"></svg><div class="paper-trunk" id="paper-trunk"><header>{draft_notice}<p class="kicker">{esc(case['category'])}</p><h1>{esc(case['title'])}</h1><p class="thesis">{esc(case['thesis'])}</p><p class="paper-title">{esc(case['paper_title'])}</p><p class="citation">{esc(case['citation'])} · <a href="https://doi.org/{esc(case['doi'])}" target="_blank" rel="noopener">论文来源 ↗</a></p><p class="audience">{esc(case['audience'])}</p><p class="paper-tip">主干与侧枝都在这张纸上。点击分叉，镜头沿连线移过去；滚轮阅读，空白处直接拖动；文字可选择，空格加拖拽可移动任意位置，Ctrl加滚轮缩放。</p></header>
<div class="body-tree-viewport" id="body-tree-viewport"><div class="story-body-tree spatial-tree" aria-label="故事主干和始终位于纸上的左右侧枝">{''.join(article)}</div></div>
<details class="coverage"><summary>本导读的材料覆盖与来源说明</summary><p>{esc(case['coverage'])}</p><ul>{source_list}</ul><p>图像均取自本篇正文或配套SI；“查看完整原页”按其材料格式显示完整原页或原始完整图像。导读为辅助解释，原文与原图保留各自的证据边界。</p><p>本导读为辅助阅读材料；尚未测量读者理解或阅读用时的改善。</p></details><footer class="bottom-links"><a href="{esc(case.get('home_href','index.html'))}">← 查看导读入口</a><a href="{case_id}.md">查看可核查文字稿</a><a href="#reading">回到开头 ↑</a></footer></div></div></div></article></main>
<dialog id="figure-dialog" aria-labelledby="modal-title"><div class="modal-head"><div><h2 id="modal-title">原图</h2><p id="modal-source"></p></div><div class="modal-controls"><button id="modal-crop" aria-pressed="true">图表</button><button id="modal-whole" aria-pressed="false" hidden>完整复合图</button><button id="modal-page" aria-pressed="false">完整原页</button><button id="modal-minus" aria-label="缩小图像">−</button><button id="modal-plus" aria-label="放大图像">＋</button><button id="modal-close">关闭</button></div></div><div class="image-stage" id="image-stage"><img id="modal-image" alt=""></div></dialog>
<script type="application/json" id="reader-data">{encoded}</script><script>{(SCRIPTS/'reader.js').read_text(encoding='utf-8')}</script></body></html>'''
    (ROOT/f'{case_id}.html').write_text(doc, encoding='utf-8', newline='')
    md.extend(['## 与画布一致的阅读导航', '']+[f'- [{n["code"]} · {n["title"]}](#{n["target"]})' for n in graph_nodes])
    md.extend(['','## 研究论证关系',''])
    research_nodes={n['id']:n for n in case['nodes']}
    for edge in case['edges']:
        a,b=research_nodes[edge['from']],research_nodes[edge['to']]
        kind='解释/研究推进' if edge.get('kind')=='interpretation' else '证据/比较关系'
        md.append(f'- [{a["title"]}](#{a["target"]}) → {edge["label"]} → [{b["title"]}](#{b["target"]})（{kind}）')
    md.extend(['','## 本地原始材料','']+[f'- [{sources[sid].get("description",sid)}]({sources[sid]["local_href"]})' for sid in case['source_ids']]+['', '## 覆盖范围', '', case['coverage']])
    (ROOT/f'{case_id}.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    return {'id': case_id, 'paragraphs': len(paragraphs), 'sections':len(case['sections']), 'figures':len(used), 'main_story_figures':sum(f['layer']=='主线' for f in figure_entries),'question_branches':len(question_branches),'optional_panel_explanations':len(walk_steps),'composites':len(config['composites']), 'nodes':len(case['nodes']),'shared_reading_nodes':len(graph_nodes),'shared_reading_edges':len(graph_edges), 'original_pages':len(config['pages']), 'html_bytes':len(doc.encode('utf-8')), 'html_sha256':hashlib.sha256(doc.encode('utf-8')).hexdigest(), 'all_navigation_targets_valid':True}

