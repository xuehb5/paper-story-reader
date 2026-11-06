"""Build offline, prose-first readers from reviewed content and PDF assets."""
from pathlib import Path
import base64
import hashlib
import html
import json
import textwrap
LANGUAGE = 'zh'
GENERAL_READER = False
B = None
ENGLISH_UI = json.loads((Path(__file__).parent / 'i18n.en.json').read_text('utf-8'))
UI_REPLACEMENTS = sorted(ENGLISH_UI.items(), key=lambda item: len(item[0]), reverse=True)

def _t(fragment):
    """Translate only static template fragments; authored scientific text is never passed here."""
    if GENERAL_READER:
        fragment = fragment.replace('材料与化学 · 离线伴读', '研究故事 · 离线伴读')
        fragment = fragment.replace('图证索引 · 按文章脉络', '证据索引 · 按文章脉络')
        fragment = fragment.replace('按研究问题组织的图证索引', '按研究问题组织的证据索引')
    if LANGUAGE != 'en':
        return fragment
    for original, translated in UI_REPLACEMENTS:
        fragment = fragment.replace(original, translated)
    return fragment.replace('Scientific argument', 'Research argument') if GENERAL_READER else fragment
UI_FRAGMENTS = json.loads((Path(__file__).parent / 'template-fragments.json').read_text('utf-8'))
def _u(index):
    return _t(UI_FRAGMENTS[index])

ROOT = None
LINK_ASSETS = False
SCRIPTS = Path(__file__).resolve().parent
assets, sources, cases = ({}, {}, [])
esc = lambda s: html.escape(str(s), quote=True)

def data_uri(path):
    if LINK_ASSETS:
        return Path(path).as_posix()
    import mimetypes
    return 'data:' + (mimetypes.guess_type(str(path))[0] or 'image/jpeg') + ';base64,' + base64.b64encode((ROOT / path).read_bytes()).decode('ascii')

def location(asset):
    part = 'SI' if asset['source'].endswith('-si') else _u(0)
    return asset.get('locator') or f"{part}{_u(1)}{asset['page']}{_u(2)}"

def scientific_flow(case):
    nodes = {n['id']: n for n in case['nodes']}
    parts = [f"""<svg class="flow" viewBox="0 0 340 {case.get('flow_height', 540)}" role="group" aria-labelledby="flow-title"><title id="flow-title">{esc(case['short'])}{_u(3)}""", '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#97adc5"/></marker></defs>']
    for edge in case['edges']:
        a, b = (nodes[edge['from']], nodes[edge['to']])
        if a['y'] == b['y']:
            left_to_right = b['x'] > a['x']
            x1, x2 = (a['x'] + 160, b['x']) if left_to_right else (a['x'], b['x'] + 160)
            y1 = y2 = a['y'] + 34
            d = f'M{x1} {y1} L{x2} {y2}'
            label = ''
        else:
            x1, y1 = (a['x'] + 80, a['y'] + 68)
            x2, y2 = (b['x'] + 80, b['y'])
            if y2 - y1 > 150:
                side = 8 if x1 < 170 else 332
                d = f'M{x1} {y1} C{x1} {y1 + 14} {side} {y1 + 14} {side} {y1 + 32} L{side} {y2 - 24} Q{side} {y2 - 10} {x2} {y2 - 10} L{x2} {y2}'
                label = ''
            else:
                mid = (y1 + y2) / 2
                d = f'M{x1} {y1} C{x1} {mid} {x2} {mid} {x2} {y2}'
                label = f'''<text class="edge-label" x="{(x1 + x2) / 2}" y="{mid - 4}">{esc(edge['label'])}</text>'''
                if LANGUAGE == 'en':
                    lines = textwrap.wrap(edge['label'], width=17, break_long_words=False)
                    spans = ''.join((f'<tspan x="{(x1 + x2) / 2}" y="{mid - 4 - (len(lines) - 1) * 4.5 + i * 9}">{esc(line)}</tspan>' for i, line in enumerate(lines)))
                    label = f'<text class="edge-label">{spans}</text>'
        kind = ' interpretation' if edge.get('kind') == 'interpretation' else ''
        relation = edge.get('kind', 'support')
        parts.append(f'''<path class="flow-edge{kind} relation-{esc(relation)}" data-relation="{esc(relation)}" d="{d}" marker-end="url(#arrow)"><title>{esc(edge['label'])}</title></path>{label}''')
    for n in case['nodes']:
        x, y = (n['x'], n['y'])
        name = (' ' if LANGUAGE == 'en' else '').join(n['lines'])
        role = n['role']
        if n.get('figure_note'):
            role += ' · ' + n['figure_note']
        elif not case.get('story_first') and (not case.get('panel_reading')):
            section = next((s for s in case['sections'] if n['target'].startswith(s['id'] + '-')), None)
            first_fig = next((b['figure'] for b in section['blocks'] if isinstance(b, dict) and 'figure' in b), None) if section else None
            if first_fig:
                role += ' · ' + case['figures'][first_fig]['label']
        section_id = next((s['id'] for s in case['sections'] if n['target'].startswith(s['id'] + '-')), '')
        parts.append(f'''<a class="flow-node relation-node scientific-node" data-story-section="{esc(section_id)}" data-finding="{esc(n.get('finding', ''))}" href="#{esc(n['target'])}" aria-label="{esc(name)}"><title>{esc(n.get('finding', name))}</title><rect x="{x}" y="{y}" width="160" height="68" rx="7"/><text class="node-role" x="{x + 80}" y="{y + 15}">{esc(role)}</text>''')
        for i, line in enumerate(n['lines']):
            line_y = y + 31 + i * 15 if LANGUAGE == 'en' else y + 35 + i * 20
            parts.append(f'<text x="{x + 80}" y="{line_y}">{esc(line)}</text>')
        parts.append('</a>')
    parts.append('</svg>')
    return ''.join(parts)

def research_map_panel(case):
    nodes = {n['id']: n for n in case['nodes']}
    if not nodes:
        reason = esc(case.get('omit_research_graph_reason', _u(4)))
        return _u(5) + reason + '</p></details>'
    relationships = ''.join(('<li>' + esc(nodes[e['from']]['title']) + ' → <b>' + esc(e['label']) + '</b> → ' + esc(nodes[e['to']]['title']) + '</li>' for e in case['edges']))
    return _u(6) + scientific_flow(case) + _u(7) + relationships + '</ul></details></details>'

def figure_html(case, fid):
    f, a = (case['figures'][fid], assets[fid])
    si = ' si' if a['source'].endswith('-si') else ''
    whole = f'<button data-open-figure="{fid}{_u(8)}' if f.get('parent') else ''
    display = ' compact-evidence' if f.get('display') == 'compact' else ''
    return f'''<figure class="figure{si}{display}" id="figure-{fid}" tabindex="-1">\n<button class="figure-image" data-open-figure="{fid}{_u(9)}{esc(f['label'])}：{esc(f['title'])}"><img src="{data_uri(a['image'])}" alt="{esc(f['label'] + '，' + f['title'])}" width="{a['width']}" height="{a['height']}" loading="lazy" decoding="async"></button>\n<figcaption><span class="figure-label">{esc(f['label'])} · {esc(f['role'])}</span><h3 class="figure-title">{esc(f['title'])}</h3><p class="figure-caption">{esc(f['caption'])}</p>\n<div class="figure-actions"><button data-open-figure="{fid}{_u(10)}{whole}<button data-open-figure="{fid}" data-mode="page">{esc(a.get('full_view_label', _u(11)))}</button><span class="source-loc">{esc(location(a))}</span></div></figcaption></figure>'''

def render(case):
    global LANGUAGE, GENERAL_READER
    LANGUAGE = case.get('language', 'zh')
    GENERAL_READER = bool(case.get('reading_profile'))
    case_id = case['id']
    original_url = case.get('source_url') or ('https://doi.org/' + case['doi'] if case.get('doi') else sources[case['source_ids'][0]]['local_href'])
    paragraphs, used, article, md = (set(), [], [], [f"# {case['title']}", '', case['thesis'], '', f"{case['paper_title']}  ", case['citation'], original_url, '', case['audience'], ''])
    walk_steps = []
    figure_entries = []
    question_branches = []
    reading_layer = _u(12)
    branch_side_counter = 0

    def fig(fid):
        assert fid not in used, ('duplicate figure', fid)
        assert assets[fid]['source'] in case['source_ids']
        if sources[assets[fid]['source']].get('format', 'pdf') == 'pdf':
            assert 1 <= assets[fid]['page'] <= sources[assets[fid]['source']]['pages']
        used.append(fid)
        figure_entries.append({'id': fid, 'section': sec['id'], 'target': 'figure-' + fid, 'title': case['figures'][fid]['title'], 'label': case['figures'][fid]['label'], 'type': 'figure', 'number': len(figure_entries) + 1, 'layer': reading_layer})
        f, a = (case['figures'][fid], assets[fid])
        md.extend([f"![{f['label']}：{f['title']}]({a['image']})", '', f"{f['caption']}（{location(a)}）", ''])
        return figure_html(case, fid)

    def rich(block):
        typ = B.kind(block);v = block[typ];target = 'evidence-' + v['id']
        if target in paragraphs:raise ValueError('duplicate evidence target')
        paragraphs.add(target)
        figure_entries.append({'id': v['id'], 'section': sec['id'], 'target': target,
                               'title': v['title'], 'label': v['label'], 'type': typ,
                               'number': len(figure_entries) + 1, 'layer': reading_layer})
        source = sources[v['source']]
        href = source['local_href'] + ('#page=' + str(v['page']) if source.get('format') == 'pdf' else '')
        parts = [f'<section class="evidence-block evidence-{typ}" id="{target}" tabindex="-1"><header><span class="figure-label">{esc(v["label"])}</span><h3>{esc(v["title"])}</h3></header>']
        md.extend([f'<a id="{target}"></a>', '### ' + v['label'] + ' · ' + v['title'], ''])
        if typ == 'table':
            parts.append('<div class="evidence-table-scroll" tabindex="0"><table><thead><tr>' + ''.join('<th scope="col">' + esc(c) + '</th>' for c in v['columns']) + '</tr></thead><tbody>')
            for row in v['rows']:parts.append('<tr>' + ''.join('<td>' + esc(c) + '</td>' for c in row) + '</tr>')
            parts.append('</tbody></table></div><p class="evidence-caption">' + esc(v['caption']) + '</p>')
            cell = lambda x: x.replace('|', '\\|').replace('\n', ' ')
            md.extend(['| ' + ' | '.join(map(cell,v['columns'])) + ' |', '| ' + ' | '.join('---' for _ in v['columns']) + ' |'])
            md.extend('| ' + ' | '.join(map(cell,row)) + ' |' for row in v['rows'])
            md.extend(['',v['caption'],''])
        elif typ == 'equation':
            expression = B.mathml(v['mathml']) if v.get('mathml') else esc(v['expression'])
            parts.append('<div class="equation-expression" role="math" aria-label="' + esc(v['expression']) + '">' + expression + '</div><dl class="equation-variables">')
            for variable in v['variables']:parts.append('<dt>' + esc(variable['symbol']) + '</dt><dd>' + esc(variable['meaning']) + '</dd>')
            parts.append('</dl><p class="evidence-caption">' + esc(v['explanation']) + '</p>')
            md.extend(['`' + v['expression'].replace('`','') + '`',''])
            md.extend('- ' + x['symbol'] + ': ' + x['meaning'] for x in v['variables'])
            md.extend(['',v['explanation'],''])
        else:
            parts.append('<blockquote>' + esc(v['text']) + '</blockquote>')
            md.extend(['> ' + v['text'].replace('\n','\n> '),''])
            if v.get('explanation'):
                parts.append('<p class="evidence-caption">' + esc(v['explanation']) + '</p>');md.extend([v['explanation'],''])
        link_label = 'Original source' if LANGUAGE == 'en' else '查看原文'
        parts.append('<a class="evidence-source" href="' + esc(href) + '" target="_blank" rel="noopener">' + link_label + ' · ' + esc(v['locator']) + '</a></section>')
        md.extend(['[' + link_label + ' · ' + v['locator'] + '](' + href + ')',''])
        return ''.join(parts)

    def walk(w, section_id):
        step_id = w['id']
        fid = w['figure']
        f = case['figures'][fid]
        walk_steps.append({**w, 'section': section_id, 'number': len(walk_steps) + 1})
        number = len(walk_steps)
        pid = step_id + '-lead'
        assert pid not in paragraphs
        paragraphs.add(pid)
        md.extend([f"{_u(13)}{f['label']}：{w['title']}", '', f'<a id="{pid}"></a>', w['lead'], ''])
        fragment = fig(fid)
        figure_entries[-1].update(target=pid, title=w['title'], layer=reading_layer)
        label = _u(14) if case.get('story_first') else f'{_u(15)}{number:02d}'
        output = [f'''<div class="panel-step" id="step-{esc(step_id)}" data-panel="{esc(f['label'])}"><h3 class="step-heading"><span class="step-number">{label}</span><span><span class="panel-name">{esc(f['label'])}</span>{esc(w['title'])}</span></h3><p class="prose panel-lead" id="{pid}" tabindex="-1">{esc(w['lead'])}</p>''', fragment]
        for i, p in enumerate(w['paragraphs'], 1):
            body_id = f'{step_id}-explain-{i}'
            paragraphs.add(body_id)
            output.append(f'<p class="prose" id="{body_id}" tabindex="-1">{esc(p)}</p>')
            md.extend([p, ''])
        output.append('</div>')
        return ''.join(output)
    for section_number, sec in enumerate(case['sections'], 1):
        article.append(f'''<section class="article-section story-trunk" id="{sec['id']}" data-graph-node="{sec['id']}" data-story-section="{sec['id']}" aria-labelledby="heading-{sec['id']}" tabindex="-1"><span class="trunk-stage-marker" aria-hidden="true">{section_number:02d}</span><h2 id="heading-{sec['id']}">{esc(sec['title'])}</h2>''')
        md.extend([f'''<a id="{sec['id']}"></a>''', f"## {sec['title']}", ''])
        if sec.get('reading_order'):
            article.append(f"{_u(16)}{esc(sec['reading_order'])}</p>")
            md.extend([_u(17) + sec['reading_order'], ''])
        count = 0
        detail_count = 0
        side_counts = {'left': 0, 'right': 0}
        last_main_id = sec['id']
        branch_group = []
        junction_number = 0

        def flush_branch_group():
            nonlocal branch_group, junction_number
            if not branch_group:
                return
            junction_number += 1
            junction_id = f"junction-{sec['id']}-{junction_number}"
            left = ''.join((markup for side, markup, _, _ in branch_group if side == 'left'))
            right = ''.join((markup for side, markup, _, _ in branch_group if side == 'right'))

            def entrances(side):
                return ''.join((f'''<a class="branch-entry" data-open-branch="{bid}" data-side="{side}" href="#{bid}"><span class="entry-direction">{esc(next((b['code'] for b in question_branches if b['id'] == bid)))} · {(_u(18) if side == 'left' else _u(19))}</span><span>{esc(title)}</span></a>''' for s, _, bid, title in branch_group if s == side))
            article.append(f'''<div class="branch-junction" id="{junction_id}" data-story-section="{sec['id']}" data-origin="{esc(last_main_id)}"><div class="junction-entries"><div class="entry-lane entry-left">{entrances('left')}</div><span class="junction-dot" aria-hidden="true"></span><div class="entry-lane entry-right">{entrances('right')}</div></div><div class="branch-lane lane-left">{left}</div><div class="branch-lane lane-right">{right}</div></div>''')
            branch_group = []
        for block in sec['blocks']:
            if not (isinstance(block, dict) and 'detail' in block):
                flush_branch_group()
            if isinstance(block, str):
                count += 1
                pid = f"{sec['id']}-p{count}"
                assert pid not in paragraphs
                paragraphs.add(pid)
                last_main_id = pid
                article.append(f'<p class="prose" id="{pid}" tabindex="-1">{esc(block)}</p>')
                md.extend([f'<a id="{pid}"></a>', block, ''])
            elif B.kind(block):
                article.append(rich(block))
            elif 'figure' in block:
                article.append(fig(block['figure']))
            elif 'figure_row' in block:
                article.append(f"""<div class="figure-row" style="--figure-columns:{len(block['figure_row'])}{_u(20)}""" + ''.join((fig(fid) for fid in block['figure_row'])) + '</div>')
            elif 'walkthrough' in block:
                article.append(walk(block['walkthrough'], sec['id']))
            else:
                detail = block['detail']
                detail_count += 1
                branch_id = f"branch-{sec['id']}-{detail_count}"
                first_step = next((b['walkthrough'] for b in detail.get('blocks', []) if 'walkthrough' in b), None)
                branch_target = first_step['id'] + '-lead' if first_step else branch_id
                evidence_ids = [b['walkthrough']['figure'] for b in detail.get('blocks', []) if 'walkthrough' in b]
                if detail.get('figure'):
                    evidence_ids.append(detail['figure'])
                evidence_ids.extend(detail.get('figures', []))
                detail_class = ('supplement' if detail.get('kind') == 'si' else 'local-reading') if GENERAL_READER else ('local-reading' if detail.get('kind') == 'figure-reading' else 'supplement')
                side = detail.get('side') or ('left' if branch_side_counter % 2 == 0 else 'right')
                side_counts[side] += 1
                code = f"{section_number:02d}·{(_u(21) if side == 'left' else _u(22))}{side_counts[side]}"
                branch_labels = [case['figures'][fid]['label'] for fid in evidence_ids] + [inner[B.kind(inner)]['label'] for inner in detail.get('blocks',[]) if B.kind(inner)]
                question_branches.append({'id': branch_id, 'section': sec['id'], 'target': branch_id, 'detail_target': branch_target, 'title': detail['title'], 'evidence': '、'.join(dict.fromkeys(branch_labels)), 'side': side, 'code': code, 'origin': last_main_id, 'kind': 'si' if detail_class == 'supplement' else 'explanation'})
                branch_side_counter += 1
                detail_start = len(article)
                article.append(f'''<section class="{detail_class} story-detail branch-{side}" id="{branch_id}" data-graph-node="{branch_id}" data-graph-code="{esc(code)}" data-side="{side}" data-branch-id="{branch_id}" data-story-section="{sec['id']}" tabindex="-1"><h3 class="branch-heading"><small class="leaf-kind"><span class="graph-code">{esc(code)}</span> · {(_u(23) if detail_class == 'supplement' else _u(24))}</small><span class="branch-title">{esc(detail['title'])}</span></h3>''')
                reading_layer = _u(25)
                md.extend([f'<a id="{branch_id}"></a>', '<details>', f"<summary>{esc(code)} · {esc(detail['title'])}</summary>", ''])
                for p in detail.get('paragraphs', []):
                    article.append(f'<p>{esc(p)}</p>')
                    md.extend([p, ''])
                if detail.get('figure'):
                    article.append(fig(detail['figure']))
                for fid in detail.get('figures', []):
                    article.append(fig(fid))
                for inner in detail.get('blocks', []):
                    article.append(rich(inner) if B.kind(inner) else walk(inner['walkthrough'], sec['id']))
                article.append(f'''<a class="return-trunk" data-story-section="{sec['id']}" href="#{esc(last_main_id)}{_u(26)}''')
                reading_layer = _u(12)
                md.extend(['</details>', ''])
                branch_group.append((side, ''.join(article[detail_start:]), branch_id, detail['title']))
                del article[detail_start:]
        flush_branch_group()
        refs = '；'.join(sec['refs'])
        article.append(f'{_u(27)}{esc(refs)}</p></section>')
        md.extend([f'{_u(28)}{refs}', ''])
    assert set(used) == set(case['figures']), ('unused figures', set(case['figures']) - set(used))
    for n in case['nodes']:
        assert n['target'] in paragraphs, ('missing paragraph', n)
    node_ids = {n['id'] for n in case['nodes']}
    assert len(node_ids) == len(case['nodes'])
    for e in case['edges']:
        assert e['from'] in node_ids and e['to'] in node_ids
    graph_nodes = []
    for index, sec in enumerate(case['sections'], 1):
        original = next((n for n in case['nodes'] if n['target'].startswith(sec['id'] + '-')), None)
        figure_labels = list(dict.fromkeys((f['label'] for f in figure_entries if f['section'] == sec['id'] and f['layer'] == _u(12))))
        graph_nodes.append({'id': sec['id'], 'type': 'main', 'section': sec['id'], 'target': sec['id'], 'title': sec['title'], 'code': f'{index:02d}', 'figures': '、'.join(figure_labels), 'finding': original.get('finding', '') if original else ''})
    graph_nodes.extend(({'id': b['id'], 'type': 'branch', 'section': b['section'], 'target': b['target'], 'title': b['title'], 'code': b['code'], 'figures': b['evidence'], 'side': b['side'], 'origin': b['origin'], 'kind': b['kind']} for b in question_branches))
    main_nodes = [n for n in graph_nodes if n['type'] == 'main']
    graph_edges = [{'from': a['id'], 'to': b['id'], 'kind': 'reading-order', 'label': _u(29)} for a, b in zip(main_nodes, main_nodes[1:])]
    graph_edges.extend(({'from': b['section'], 'to': b['id'], 'origin': b['origin'], 'kind': 'branch', 'label': _u(30) if b['kind'] == 'si' else _u(31)} for b in question_branches))
    assert len({n['id'] for n in graph_nodes}) == len(graph_nodes)
    assert all((n['target'] in {s['id'] for s in case['sections']} | paragraphs | {b['id'] for b in question_branches} for n in graph_nodes))
    config = {'language': LANGUAGE, 'ui': ENGLISH_UI if LANGUAGE == 'en' else {}, 'assetMode': 'linked' if LINK_ASSETS else 'embedded', 'figures': {}, 'pages': {}, 'composites': {}, 'researchGraph': {'nodes': case['nodes'], 'edges': case['edges']}, 'readingGraph': {'nodes': graph_nodes, 'edges': graph_edges}}
    identity = {'id': case['id'], 'title': case['title'], 'sections': case['sections'], 'figures': case['figures'], 'sources': {sid: sources[sid]['sha256'] for sid in case['source_ids']}}
    config['readerIdentity'] = hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:24]
    (ROOT / 'graphs').mkdir(exist_ok=True)
    (ROOT / 'graphs' / f'{case_id}.reading-graph.json').write_text(json.dumps(config['readingGraph'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'graphs' / f'{case_id}.research-graph.json').write_text(json.dumps(config['researchGraph'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for fid in used:
        a, f = (assets[fid], case['figures'][fid])
        page_key = f"{a['source']}-{a['page']}"
        config['figures'][fid] = {**f, 'location': location(a), 'page_key': page_key, 'full_view_label': a.get('full_view_label', _u(11)), 'full_view_description': a.get('full_view_description', _u(32))}
        if page_key not in config['pages']:
            config['pages'][page_key] = data_uri(a['page_image'])
        if f.get('parent'):
            parent = f['parent']
            assert assets[parent]['source'] == a['source'] and assets[parent]['page'] == a['page']
            config['composites'][parent] = {**case['composites'][parent], 'image': data_uri(assets[parent]['image'])}
    panel_outline = ''
    if figure_entries:
        outline_steps = [{**w, 'fid': w['id']} for w in figure_entries]
        groups = []
        for sec in case['sections']:
            steps = [w for w in outline_steps if w['section'] == sec['id']]
            if not steps:
                continue
            links = ''.join((f'''<li><a class="outline-link" data-story-section="{esc(sec['id'])}" href="#{esc(w['target'])}"><span class="outline-number">{esc(w['layer'])}</span><span><b>{esc(w['label'])}</b><small>{esc(w['title'])}</small></span></a></li>''' for w in steps))
            groups.append(f"""<details class="panel-group"><summary>{esc(sec['title'])}</summary><ol>{links}</ol></details>""")
        outline_title = _u(33)
        hint = _u(34)
        panel_outline = f"""<details class="panel-outline route-card" id="panel-nav"><summary>{outline_title}</summary><p>{hint}{_u(35)}{''.join(groups)}</nav></details>"""
    route_open = ' open'
    route_summary = _u(36)
    encoded = json.dumps(config, ensure_ascii=False, separators=(',', ':')).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    tabs = ''.join((f'''<a href="{esc(c.get('href', c['id'] + '.html'))}"''' + (' aria-current="page"' if c['id'] == case_id else '') + f">{esc(c['short'])}</a>" for c in cases))
    source_list = ''.join(('<li>' + esc(sources[sid].get('description') or _u(37)) + ' · <a href="' + esc(sources[sid]['local_href']) + _u(38) for sid in case['source_ids']))
    draft_notice = '<p class="paper-tip" role="status">' + esc(case['draft_notice']) + '</p>' if case.get('draft_notice') else ''
    if case.get('draft_notice'):
        md[0:0] = [case['draft_notice'], '']
    doc = f'''<!doctype html><html lang="{LANGUAGE}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(case['title'])}{_u(39)}{(SCRIPTS / 'reader.css').read_text(encoding='utf-8')}{(SCRIPTS / 'evidence.css').read_text(encoding='utf-8')}{_u(40)}{esc(case.get('home_href', 'index.html'))}{_u(41)}{tabs}{_u(42)}{route_open}><summary>{route_summary}{_u(43)}{''.join((f"""<a href="#{esc(n['target'])}">{esc(n['code'])} · {esc(n['title'])}</a>""" for n in graph_nodes))}{_u(44)}{research_map_panel(case)}</details>{panel_outline}{_u(45)}{draft_notice}<p class="kicker">{esc(case['category'])}</p><h1>{esc(case['title'])}</h1><p class="thesis">{esc(case['thesis'])}</p><p class="paper-title">{esc(case['paper_title'])}</p><p class="citation">{esc(case['citation'])} · <a href="{esc(original_url)}{_u(46)}{esc(case['audience'])}{_u(47)}{''.join(article)}{_u(48)}{esc(case['coverage'])}</p><ul>{source_list}{_u(49)}{esc(case.get('home_href', 'index.html'))}{_u(50)}{case_id}{_u(51)}{encoded}</script><script>{(SCRIPTS / 'reader.js').read_text(encoding='utf-8')}</script></body></html>'''
    (ROOT / f'{case_id}.html').write_text(doc, encoding='utf-8', newline='')
    md.extend([_u(52), ''] + [f"- [{n['code']} · {n['title']}](#{n['target']})" for n in graph_nodes])
    md.extend(['', _u(53), ''])
    research_nodes = {n['id']: n for n in case['nodes']}
    for edge in case['edges']:
        a, b = (research_nodes[edge['from']], research_nodes[edge['to']])
        kind = edge.get('kind', 'support') if GENERAL_READER else (_u(54) if edge.get('kind') == 'interpretation' else _u(55))
        md.append(f"- [{a['title']}](#{a['target']}) → {edge['label']} → [{b['title']}](#{b['target']})（{kind}）")
    md.extend(['', _u(56), ''] + [f"- [{sources[sid].get('description', sid)}]({sources[sid]['local_href']})" for sid in case['source_ids']] + ['', _u(57), '', case['coverage']])
    (ROOT / f'{case_id}.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    return {'id': case_id, 'paragraphs': len(paragraphs), 'sections': len(case['sections']), 'figures': len(used), 'main_story_figures': sum((f['type'] == 'figure' and f['layer'] == _u(12) for f in figure_entries)), 'question_branches': len(question_branches), 'optional_panel_explanations': len(walk_steps), 'composites': len(config['composites']), 'nodes': len(case['nodes']), 'shared_reading_nodes': len(graph_nodes), 'shared_reading_edges': len(graph_edges), 'original_pages': len(config['pages']), 'html_bytes': len(doc.encode('utf-8')), 'html_sha256': hashlib.sha256(doc.encode('utf-8')).hexdigest(), 'all_navigation_targets_valid': True}
