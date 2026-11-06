"""Build a portable single-paper reader from evidence-reviewed JSON. No model API required."""
import argparse, copy, hashlib, html, importlib.util, json, re, shutil, textwrap
from pathlib import Path

SKILL=Path(__file__).resolve().parents[1]
DEFAULT_LANGUAGE=json.loads((SKILL/'reader-defaults.json').read_text('utf-8')).get('language','zh') if (SKILL/'reader-defaults.json').exists() else 'zh'
def local_module(name):
    spec=importlib.util.spec_from_file_location('reader_'+name,SKILL/'scripts'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
P=local_module('reading_profiles');B=local_module('content_blocks')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(input_file,output,review_file=None,draft=False,context_file=None,link_assets=False):
    input_file=Path(input_file).resolve();base=input_file.parent
    data=json.loads(input_file.read_text(encoding='utf-8'));case=copy.deepcopy(data['case'])
    language=case.get('language',DEFAULT_LANGUAGE).split('-')[0].lower()
    if language not in ['zh','en']:raise ValueError('supported reader languages are zh and en')
    case['language']=language
    profile=P.resolve(case)
    assets=copy.deepcopy(data['assets']);sources=copy.deepcopy(data['sources']);output=Path(output).resolve()
    material_errors=P.validate_materials(case,sources)
    if material_errors:raise ValueError('; '.join(material_errors))
    if case.get('source_url'):
        from urllib.parse import urlparse
        url=urlparse(case['source_url'])
        if url.scheme!='https' or not url.hostname or url.username or url.password:raise ValueError('source_url must be an ordinary HTTPS source URL')
    if output.exists() and any(output.iterdir()):raise ValueError('output directory must be empty; use a new revision directory to retain previous builds and failures')
    review_path=Path(review_file).resolve() if review_file else base/'evidence-review.json'
    review_result=None;release_result=None
    if not draft:
        if not review_path.is_file():raise ValueError('source review required: prepare evidence-review.json and pass --review; use --draft only for labelled preview')
        spec=importlib.util.spec_from_file_location('evidence_check',SKILL/'scripts/validate_evidence.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        review_result=checker.validate_review(input_file,review_path)
        if not review_result['passed']:raise ValueError('source review blocks final build: '+'; '.join(review_result['errors'][:12]))
        context_path=Path(context_file).resolve() if context_file else base/'context-audit.json'
        if not context_path.is_file():raise ValueError('context-audit.json required for final build; read references/release-check.md; --draft remains a labelled preview')
        spec=importlib.util.spec_from_file_location('release_check',SKILL/'scripts/validate_release.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
        release_result=release.validate(input_file,review_path,context_path)
        if not release_result['passed']:raise ValueError('context/wording/encoding blocks final build: '+'; '.join(release_result['errors'][:12]))
    else:
        case['draft_notice']=('Draft: source review is incomplete. Content may be incorrect and must not be presented as reviewed.' if language=='en' else '草稿：来源核查尚未完成，内容可能有误，不能作为已复核读本。')
    required=['id','short','title','category','paper_title','citation','thesis','audience','coverage']
    for key in required:
        if not isinstance(case.get(key),str) or not case[key].strip():raise ValueError('case: missing '+key)
    safe=lambda value:bool(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',value))
    if not safe(case['id']):raise ValueError('case id must be a safe filename/HTML id')
    if not case.get('sections'):raise ValueError('sections must be nonempty')
    section_ids=[s['id'] for s in case['sections']]
    if len(set(section_ids))!=len(section_ids) or any(not safe(i) for i in section_ids):raise ValueError('invalid/duplicate section id')
    if not case.get('source_ids') or set(case['source_ids'])!=set(sources):raise ValueError('source_ids do not match sources')
    resolved={}
    for sid,source in sources.items():
        p=(base/source['file']).resolve()
        if not p.is_file():raise ValueError('missing source '+sid)
        if digest(p)!=source['sha256']:raise ValueError('source hash mismatch '+sid)
        if not source.get('description'):raise ValueError('source description required: state PDF pages or JATS/HTML locator')
        source['file']=str(p);resolved[sid]=p
    figures=case.get('figures',{});used=[]
    def check_figure(fid):
        if fid not in figures or fid not in assets:raise ValueError('unknown figure '+fid)
        if not safe(fid):raise ValueError('unsafe figure id '+fid)
        used.append(fid)
    paragraph_targets={s['id']+f'-p{n}' for s in case['sections'] for n in range(1,1+sum(isinstance(b,str) for b in s['blocks']))}
    walkthrough_ids=set()
    rich_ids=set()
    def check_rich(block):
        value=B.validate(block,sources,safe)
        if value['id'] in rich_ids:raise ValueError('duplicate rich evidence id')
        rich_ids.add(value['id'])
    def check_walk(w):
        if not safe(w.get('id','')) or w['id'] in walkthrough_ids:raise ValueError('invalid/duplicate walkthrough id')
        walkthrough_ids.add(w['id'])
        if not w.get('title') or not w.get('lead') or not w.get('paragraphs'):raise ValueError('walkthrough requires title, lead and paragraphs')
        check_figure(w['figure'])
    for sec in case['sections']:
        if not sec.get('title') or not sec.get('refs') or not any(isinstance(b,str) and b.strip() for b in sec.get('blocks',[])):raise ValueError('section requires title, prose and refs: '+sec['id'])
        for block in sec['blocks']:
            if isinstance(block,str):continue
            if B.kind(block):check_rich(block)
            elif set(block)=={'figure'}:check_figure(block['figure'])
            elif set(block)=={'figure_row'}:
                for fid in block['figure_row']:check_figure(fid)
            elif set(block)=={'walkthrough'}:check_walk(block['walkthrough'])
            elif set(block)=={'detail'}:
                d=block['detail']
                if not d.get('title') or not (d.get('paragraphs') or d.get('blocks')) or d.get('side') not in ['left','right']:raise ValueError('detail requires title, prose or walkthrough blocks, and side')
                if d.get('figure'):check_figure(d['figure'])
                for fid in d.get('figures',[]):check_figure(fid)
                for inner in d.get('blocks',[]):
                    if B.kind(inner):check_rich(inner)
                    elif isinstance(inner,dict) and set(inner)=={'walkthrough'}:check_walk(inner['walkthrough'])
                    else:raise ValueError('detail blocks accept walkthrough or rich evidence records')
            else:raise ValueError('unsupported block '+str(block.keys()))
    if len(used)!=len(set(used)):raise ValueError('duplicate figure occurrence id: give repeated use a unique id pointing to the same image')
    if set(used)!=set(figures):raise ValueError('unused or missing figure metadata')
    reserved=set(section_ids)|paragraph_targets|{'figure-'+fid for fid in figures}
    if any('evidence-'+ident in reserved for ident in rich_ids):raise ValueError('rich evidence id collides with another reader target')
    composites=case.get('composites',{})
    parents={f['parent'] for f in figures.values() if f.get('parent')}
    if parents!=set(composites):raise ValueError('composite metadata must match referenced parent figures')
    for parent in parents:
        if not safe(parent) or parent not in assets or not composites[parent].get('label') or not composites[parent].get('title'):raise ValueError('invalid composite '+parent)
    for fid in used+sorted(parents):
        f=figures.get(fid);a=assets[fid]
        if f:
            for k in ['label','title','role','caption']:
                if not f.get(k):raise ValueError(fid+': missing '+k)
        if a.get('source') not in sources:raise ValueError(fid+': unknown source')
        if not a.get('locator'):raise ValueError(fid+': explicit PDF or JATS locator required')
        if sources[a['source']].get('format')=='jats' and a.get('full_view_description') not in ['完整原始图像','Complete original image']:raise ValueError(fid+': JATS must identify the complete original image, not invent PDF pages')
        for key in ['image','page_image']:
            p=(base/a[key]).resolve()
            if not p.is_file():raise ValueError(fid+': missing '+key)
            expected=a.get('sha256' if key=='image' else 'page_sha256')
            if not expected or digest(p)!=expected:raise ValueError(fid+': missing or mismatched image hash')
            a[key]=str(p)
        if any(not isinstance(a.get(k),(int,float)) or a[k]<=0 for k in ['width','height']):raise ValueError(fid+': missing image dimensions')
    for fid in used:
        parent=figures[fid].get('parent')
        if parent and any(assets[fid][k]!=assets[parent][k] for k in ['source','page']):raise ValueError(fid+': parent source/page mismatch')
    # Reading order and scientific argument are distinct, explicitly authored graphs.
    graph=case.get('research_graph')
    if graph is not None:
        nodes=[]
        for n in graph.get('nodes',[]):
            title=n.get('title','');column=n.get('column','center');row=n.get('row')
            if not title or column not in ['left','right','center'] or not isinstance(row,int) or row<0:raise ValueError('research node requires title, row and column')
            lines=textwrap.wrap(title,width=21,break_long_words=True,break_on_hyphens=False) if language=='en' else [title[i:i+9] for i in range(0,len(title),9)]
            nodes.append({**n,'lines':lines,'x':{'left':5,'center':90,'right':175}[column],'y':12+row*112})
        case['nodes']=nodes;case['edges']=graph.get('edges',[]);case['flow_height']=max((n['y']+92 for n in nodes),default=100)
        rows={n['row'] for n in nodes}
        for row in rows:
            columns=[n['column'] for n in nodes if n['row']==row]
            if len(columns)!=len(set(columns)) or ('center' in columns and len(columns)>1):raise ValueError('overlapping research nodes in row '+str(row))
    else:case['nodes']=case.get('nodes',[]);case['edges']=case.get('edges',[])
    node_ids=[n.get('id') for n in case['nodes']]
    if len(node_ids)!=len(set(node_ids)) or any(not isinstance(n,str) or not safe(n) for n in node_ids):raise ValueError('invalid/duplicate research node id')
    for node in case['nodes']:
        if node.get('target') not in paragraph_targets:raise ValueError('research target must be an existing prose paragraph')
        if not node.get('role') or not node.get('finding'):raise ValueError('research node requires role and finding')
        if len(node.get('lines',[]))>(3 if language=='en' else 2):raise ValueError('research title too long; use a short label and full finding')
    for edge in case['edges']:
        if edge.get('from') not in node_ids or edge.get('to') not in node_ids or not edge.get('label') or edge['from']==edge['to']:raise ValueError('invalid/unlabelled research relationship')
        if not profile['legacy'] and edge.get('kind') not in P.EDGE_TYPES:raise ValueError('unknown typed argument relationship')
    if not case['nodes'] and not case.get('omit_research_graph_reason'):raise ValueError('research graph missing: provide an authored graph or explicit omission reason')
    navigation=data.get('navigation',{})
    def safe_href(value):
        return isinstance(value,str) and bool(value) and not re.search(r'[:\\<>"\x00-\x20]',value) and not value.startswith(('/','#'))
    if navigation:
        if not safe_href(navigation.get('home','')):raise ValueError('navigation home must be a relative HTML path')
        for entry in navigation.get('papers',[]):
            if not safe_href(entry.get('href','')) or not entry.get('short') or not safe(entry.get('id','')):raise ValueError('invalid collection entry')
        if not any(entry['id']==case['id'] for entry in navigation.get('papers',[])):raise ValueError('collection must include current paper')
        case['home_href']=navigation['home']
    case['story_first']=True;case['composites']=composites
    case['source_ids']=list(sources)
    spec=importlib.util.spec_from_file_location('reader_core',SKILL/'assets/reader/render_core.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    output.mkdir(parents=True,exist_ok=True);(output/'assets').mkdir(exist_ok=True)
    (output/'sources').mkdir(exist_ok=True)
    for sid,source in sources.items():
        src=resolved[sid];dest=output/'sources'/(digest(src)[:20]+src.suffix.lower())
        if src!=dest:shutil.copy2(src,dest)
        source['local_href']=dest.relative_to(output).as_posix()
    for fid in used+sorted(parents):
        a=assets[fid]
        for key in ['image','page_image']:
            src=Path(a[key]);dest=output/'assets'/(digest(src)[:20]+src.suffix.lower())
            if src!=dest:shutil.copy2(src,dest)
            a[key]=dest.relative_to(output).as_posix()
    core.ROOT=output;core.assets=assets;core.sources=sources;core.cases=navigation.get('papers') or [case];core.LINK_ASSETS=link_assets;core.B=B
    report=core.render(case)
    entry=case['id']+'.html'+('?v=0.24.0' if link_assets else '')
    entry_label='Open the interactive reader: ' if language=='en' else '打开交互读本：'
    (output/'index.html').write_text('<!doctype html><html lang="'+language+'"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url='+entry+'"><title>PaperStory · '+html.escape(case['title'])+'</title><a href="'+entry+'">'+entry_label+html.escape(case['title'])+'</a></html>',encoding='utf-8')
    report.update({'renderer_version':'v0.24.0','language':language,'reading_profile':profile,'rich_evidence_blocks':len(rich_ids),'input_sha256':digest(input_file),'source_hashes_verified':True,'images_hashes':{fid:digest(output/a['image']) for fid,a in assets.items() if fid in used},'asset_mode':'linked' if link_assets else 'embedded','external_runtime_dependencies':0,'scientific_sufficiency_automatically_judged':False,'content_review_status':'draft_unreviewed' if draft else 'review_record_complete','source_review':review_result,'context_review':release_result})
    (output/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('verify_delivery',SKILL/'scripts/verify_delivery.py');delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
    encoding=delivery.verify([output/(case['id']+'.html'),output/(case['id']+'.md')],case.get('language','zh'))
    if not encoding['passed']:raise ValueError('generated delivery encoding invalid: '+'; '.join(encoding['errors']))
    files={p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file() and p.name!='delivery-manifest.json'}
    (output/'delivery-manifest.json').write_text(json.dumps({'renderer_version':'v0.24.0','input_sha256':digest(input_file),'files':files,'notice':'Any later byte change requires regeneration and renewed review for content changes. Hashes verify bytes, not scientific truth.'},ensure_ascii=False,indent=2)+'\n','utf-8')
    return report
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('--output',required=True);p.add_argument('--review');p.add_argument('--context-audit');p.add_argument('--draft',action='store_true');p.add_argument('--link-assets',action='store_true',help='Use local relative image files for static web hosting; keep the generated directory together. The reader UI is unchanged.');a=p.parse_args()
    try:print(json.dumps(build(a.input,a.output,a.review,a.draft,a.context_audit,a.link_assets),ensure_ascii=False));return 0
    except (ValueError,KeyError,TypeError,AttributeError,OSError,AssertionError) as e:print(json.dumps({'passed':False,'error':str(e)},ensure_ascii=False));return 1
if __name__=='__main__':raise SystemExit(main())
