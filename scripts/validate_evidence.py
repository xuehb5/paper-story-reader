"""Check provenance, review coverage and canonical graph claims, not scientific entailment."""
import argparse,hashlib,importlib.util,json,re,unicodedata,xml.etree.ElementTree as ET
from pathlib import Path

LEVELS={'observation','derived','model_result','author_interpretation','author_claim','background','synthesis',
        'formal_result','assumption','qualitative_finding','textual_interpretation'}

def local_module(name):
    spec=importlib.util.spec_from_file_location('paperstory_'+name,Path(__file__).parent/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
P=local_module('reading_profiles');B=local_module('content_blocks')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(text):return ' '.join(unicodedata.normalize('NFKC',text).split())
def text_sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def pointer(parts):return '/'+ '/'.join(str(p).replace('~','~0').replace('/','~1') for p in parts)

def navigation_pointer(value):
    """Allow headings/metadata, never substantive prose, cells, formulas or findings."""
    if value in ['/case/title','/case/coverage']:return True
    if re.search(r'/(?:table|equation|quotation)/',value):return False
    return value.endswith(('/title','/label','/role')) or bool(re.fullmatch(r'/case/(?:research_graph/)?edges/\d+/kind',value))

def content_units(data):
    """Enumerate visible scientific text. New unknown block types fail instead of silently escaping review."""
    units={};case=data['case']
    def add(parts,value):
        if isinstance(value,str) and value.strip():units[pointer(parts)]=value
    def fields(obj,parts,keys):
        for key in keys:
            if key in obj:add(parts+[key],obj[key])
    def walk(w,parts):
        fields(w,parts,['title','lead'])
        for i,p in enumerate(w.get('paragraphs',[])):add(parts+['paragraphs',i],p)
    def rich(block,parts):
        typ=B.kind(block)
        for suffix,text in B.visible_units(typ,block[typ]):add(parts+[typ]+suffix,text)
    fields(case,['case'],['title','thesis','coverage'])
    for i,s in enumerate(case.get('sections',[])):
        parts=['case','sections',i];fields(s,parts,['title'])
        for j,b in enumerate(s.get('blocks',[])):
            p=parts+['blocks',j]
            if isinstance(b,str):add(p,b)
            elif B.kind(b):rich(b,p)
            elif set(b)=={'walkthrough'}:walk(b['walkthrough'],p+['walkthrough'])
            elif set(b)=={'detail'}:
                d=b['detail'];p+=['detail'];fields(d,p,['title'])
                for k,value in enumerate(d.get('paragraphs',[])):add(p+['paragraphs',k],value)
                for k,inner in enumerate(d.get('blocks',[])):
                    if B.kind(inner):rich(inner,p+['blocks',k])
                    elif isinstance(inner,dict) and set(inner)=={'walkthrough'}:walk(inner['walkthrough'],p+['blocks',k,'walkthrough'])
                    else:raise ValueError('unknown detail block: '+pointer(p))
            elif not isinstance(b,dict) or set(b) not in ({'figure'},{'figure_row'}):raise ValueError('unknown content block: '+pointer(p))
    for key in ['figures','composites']:
        for ident,fig in case.get(key,{}).items():fields(fig,['case',key,ident],['title','role','caption'])
    graph=case.get('research_graph') or {'nodes':case.get('nodes',[]),'edges':case.get('edges',[])}
    gp=['case','research_graph'] if 'research_graph' in case else ['case']
    for i,node in enumerate(graph.get('nodes',[])):fields(node,gp+['nodes',i],['title','role','finding'])
    for i,edge in enumerate(graph.get('edges',[])):fields(edge,gp+['edges',i],['label','kind'])
    if case.get('omit_research_graph_reason'):add(['case','omit_research_graph_reason'],case['omit_research_graph_reason'])
    return units

def initialize(input_file):
    path=Path(input_file);data=json.loads(path.read_text('utf-8'))
    return {'schema_version':1,'input_sha256':sha(path),'claims':[],
        'units':[{'pointer':p,'text_sha256':text_sha(t),'kind':'factual','claim_ids':[],'verdict':'pending','reason':''} for p,t in content_units(data).items()],
        'reviewer':{'method':'','identity':'','source_first_summary':'','unresolved_items':[]}}

def validate_review(input_file,review_file):
    path=Path(input_file).resolve();base=path.parent;data=json.loads(path.read_text('utf-8'));review=json.loads(Path(review_file).read_text('utf-8'));errors=[]
    def fail(message):errors.append(message)
    def required(obj,keys,where):
        for key in keys:
            if not isinstance(obj.get(key),str) or not obj[key].strip():fail(where+': missing '+key)
    profile=P.resolve(data['case'])
    errors.extend(P.validate_materials(data['case'],data.get('sources',{})))
    if review.get('schema_version')!=1:fail('review schema_version must be 1')
    if review.get('input_sha256')!=sha(path):fail('review is stale: input SHA-256 changed; re-review changed content')
    source_text={};source_anchors={};source_records=data.get('sources',{});assets=data.get('assets',{});valid_assets=set()
    if set(data['case'].get('source_ids',[]))!=set(source_records):fail('case source_ids do not match provided sources')
    for sid,s in source_records.items():
        file=(base/s.get('file','')).resolve()
        if not file.is_file() or sha(file)!=s.get('sha256'):fail('source missing or hash changed: '+sid);continue
        try:
            if s.get('format')=='jats':
                root=ET.parse(file).getroot()
                dois=[norm(''.join(e.itertext())).lower() for e in root.iter() if e.tag.rsplit('}',1)[-1]=='article-id' and e.get('pub-id-type')=='doi']
                if dois and data['case'].get('doi') and data['case']['doi'].lower().strip() not in dois:fail('source DOI differs from reader paper: '+sid)
                # Ignore inline SVG drawing metadata in text matching; retain actual source untouched.
                for parent in root.iter():
                    for child in list(parent):
                        if child.tag.rsplit('}',1)[-1]=='svg':parent.remove(child)
                source_text[sid]=[norm(' '.join(root.itertext()))]
                source_anchors[sid]={}
                for element in root.iter():
                    if element.get('id'):source_anchors[sid].setdefault(element.get('id'),[]).append(norm(' '.join(element.itertext())))
            elif s.get('format')=='pdf':source_text[sid]=None  # Read only if a text quote uses this PDF.
            elif s.get('format')=='text':source_text[sid]=[norm(file.read_text('utf-8'))]
            elif s.get('format')=='image':pass  # Original standalone supplemental image; actual-view evidence only.
            else:fail('unsupported source format for evidence: '+sid)
        except (ET.ParseError,OSError,ValueError) as e:fail('cannot read source '+sid+': '+str(e))
    for aid,a in assets.items():
        if a.get('source') not in source_records:fail('unknown asset source: '+aid);continue
        okay=True
        for key,hkey in [('image','sha256'),('page_image','page_sha256')]:
            file=(base/a.get(key,'')).resolve()
            if not file.is_file() or sha(file)!=a.get(hkey):fail('asset missing or hash changed: '+aid+'/'+key);okay=False
        if okay:valid_assets.add(aid)
    claims={};evidence_count=0;visual_hashes=set()
    for claim in review.get('claims',[]):
        ident=claim.get('id','');where='claim '+str(ident)
        if not ident or ident in claims:fail('empty/duplicate claim id: '+str(ident));continue
        claims[ident]=claim
        required(claim,['statement','subject','conditions','scope','support','limit'],where)
        if claim.get('level') not in LEVELS:fail(where+': unknown evidence level')
        if claim.get('level')=='formal_result':
            if 'theoretical' not in profile['study_types']:fail(where+': formal_result requires a theoretical reading route')
            if claim.get('formal_status') not in ['proved_in_source','stated_without_proof','conjecture']:fail(where+': record the original formal status')
            if not isinstance(claim.get('assumptions'),list) or not claim['assumptions'] or any(not isinstance(x,str) or not x.strip() for x in claim['assumptions']):fail(where+': record actual formal assumptions')
            if not any(e.get('kind')=='text' for e in claim.get('evidence',[])):fail(where+': formal_result needs original text evidence')
        if not claim.get('evidence'):fail(where+': no evidence')
        for ev in claim.get('evidence',[]):
            evidence_count+=1
            if ev.get('kind')=='figure':
                if ev.get('asset') not in valid_assets:fail(where+': invalid figure evidence asset')
                else:visual_hashes.add(assets[ev['asset']]['sha256'])
                required(ev,['panels','axes','legend','conditions','observation'],where+' figure')
            elif ev.get('kind')=='text':
                sid=ev.get('source');s=source_records.get(sid,{});required(ev,['locator','quote'],where+' text')
                if sid not in source_text:fail(where+': unavailable text source');continue
                if s.get('format')=='pdf':
                    page=ev.get('page')
                    if not isinstance(page,int) or isinstance(page,bool) or page<1:fail(where+': PDF physical page required');continue
                    if source_text[sid] is None:
                        try:
                            from pypdf import PdfReader
                            source_text[sid]=[norm(p.extract_text() or '') for p in PdfReader(base/s['file']).pages]
                        except (ImportError,ValueError,OSError) as e:fail(where+': PDF text extraction unavailable; use actual page-image evidence: '+str(e));continue
                    pages=source_text[sid]
                    if not pages or page>len(pages):fail(where+': PDF page outside source');continue
                    content=pages[page-1]
                else:
                    if 'page' in ev:fail(where+': do not assign PDF pages to non-PDF sources')
                    content=source_text[sid][0]
                if 'anchor' in ev:
                    anchor=ev['anchor'];matches=source_anchors.get(sid,{}).get(anchor,[]) if isinstance(anchor,str) else []
                    if s.get('format')!='jats' or len(matches)!=1:
                        fail(where+': declared source anchor is missing, ambiguous or unsupported');continue
                    content=matches[0]
                if len(norm(ev.get('quote','')))<8 or norm(ev.get('quote','')) not in content:fail(where+': quoted text does not match original source at the declared page')
                if 'anchor' in ev and norm(ev.get('quote','')) not in content:fail(where+': quote does not belong to declared source anchor')
            else:fail(where+': unknown evidence kind')
    rich_ids=set()
    for _,block in B.walk_blocks(data['case']):
        try:
            value=B.validate(block,source_records,lambda x:bool(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',x)))
            if value['id'] in rich_ids:fail('duplicate rich evidence id: '+value['id'])
            rich_ids.add(value['id'])
            if B.kind(block)=='quotation':
                sid=value['source'];page=value.get('page');matching=[]
                for claim in claims.values():
                    matching.extend(e for e in claim.get('evidence',[]) if e.get('kind')=='text' and e.get('source')==sid and e.get('page')==page and ('anchor' not in value or e.get('anchor')==value['anchor']) and norm(value['text'])==norm(e.get('quote','')))
                if not matching:fail('quotation must exactly match a source-checked text evidence record: '+value['id'])
        except (ValueError,ET.ParseError) as e:fail(str(e))
    for aid in data['case'].get('figures',{}):
        if assets.get(aid,{}).get('sha256') not in visual_hashes:fail('displayed figure lacks actual-view record: '+aid)
    expected=content_units(data);seen={}
    for unit in review.get('units',[]):
        p=unit.get('pointer','')
        if p in seen:fail('duplicate review unit: '+p)
        seen[p]=unit
        if p not in expected:fail('review references removed/unknown unit: '+p);continue
        if unit.get('text_sha256')!=text_sha(expected[p]):fail('changed/unreviewed text unit: '+p)
        if unit.get('verdict') not in ['aligned','qualified']:fail('unit not resolved: '+p)
        required(unit,['reason'],'unit '+p)
        ids=unit.get('claim_ids',[])
        if unit.get('kind')=='factual':
            if not isinstance(ids,list) or not ids or any(i not in claims for i in ids):fail('unit missing valid claim links: '+p)
        elif unit.get('kind')=='navigation':
            if not navigation_pointer(p):fail('scientific text cannot bypass claim review as navigation: '+p)
            if ids or unit.get('verdict')!='aligned':fail('navigation must have empty claim_ids and aligned verdict: '+p)
        else:fail('unknown review unit kind: '+p)
    for p in expected.keys()-seen.keys():fail('missing review unit: '+p)
    if not claims:fail('no source-backed claims recorded')
    graph=data['case'].get('research_graph')
    if graph is None and data['case'].get('nodes'):fail('reviewed output requires research_graph or explicit omission reason; migrate legacy graph')
    for i,n in enumerate((graph or {}).get('nodes',[])):
        cid=n.get('claim_id');claim=claims.get(cid)
        if not claim:fail('graph node lacks canonical claim_id: '+str(n.get('id')));continue
        if n.get('finding')!=claim.get('statement'):fail('graph finding drifts from canonical claim: '+str(n.get('id')))
        p=f'/case/research_graph/nodes/{i}/finding'
        if cid not in seen.get(p,{}).get('claim_ids',[]):fail('graph finding unit must link canonical claim: '+p)
    for edge in (graph or {}).get('edges',[]):
        if not profile['legacy'] and edge.get('kind') not in P.EDGE_TYPES:fail('unknown typed argument relationship: '+str(edge.get('kind')))
    reviewer=review.get('reviewer',{});required(reviewer,['identity','source_first_summary'],'reviewer')
    if reviewer.get('method') not in ['independent_agent','same_agent_second_pass']:fail('source-first second review not recorded')
    if reviewer.get('pending_checks'):fail('reviewer still declares pending checks; complete them or keep output as draft')
    if not isinstance(reviewer.get('unresolved_items'),list):fail('reviewer unresolved_items must be a list')
    for item in reviewer.get('unresolved_items',[]):
        required(item,['issue','disclosure_unit'],'unresolved item')
        if seen.get(item.get('disclosure_unit'),{}).get('verdict')!='qualified':fail('unresolved source issue must be disclosed in a qualified unit')
    return {'passed':not errors,'status':'review_record_complete' if not errors else 'blocked','input_sha256':sha(path),'review_sha256':sha(review_file),'review_units':len(seen),'claims':len(claims),'evidence_items':evidence_count,'visual_images_recorded':len(visual_hashes),'review_method':reviewer.get('method'),'scientific_entailment_automatically_judged':False,'errors':errors}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');group=p.add_mutually_exclusive_group(required=True);group.add_argument('--init');group.add_argument('--review');p.add_argument('--output');a=p.parse_args()
    try:
        if a.init:
            target=Path(a.init)
            if target.exists():raise ValueError('review file already exists; preserve it and use a new path')
            target.parent.mkdir(parents=True,exist_ok=True);result=initialize(a.input);target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'status':'pending','units':len(result['units']),'file':str(target)},ensure_ascii=False));return 0
        result=validate_review(a.input,a.review)
    except (ValueError,KeyError,TypeError,AttributeError,OSError) as e:result={'passed':False,'status':'blocked','scientific_entailment_automatically_judged':False,'errors':[str(e)]}
    if a.output:Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
