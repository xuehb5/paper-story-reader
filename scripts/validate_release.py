"""Validate explicit context decisions and their visible wording, not full scientific entailment."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,re
HERE=Path(__file__).resolve().parent
def load_module(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
E=load_module('release_evidence','validate_evidence.py');V=load_module('delivery_text','verify_delivery.py')
sha=E.sha
def negated(text,pos):
    clause=re.split(r'[。！？!?；;，,：:]',text[max(0,pos-30):pos])[-1]
    english_clause=re.split(r'[.!?;,\n]',text[max(0,pos-100):pos])[-1]
    return bool(re.search(r'不(?:能|足以|等于|代表|应|意味着)?|并未|未(?!来)|无法|尚无|没有|并非|不是|而非',clause) or re.search(r"\b(?:not(?!\s+only)|never|cannot|can['’]t|no|fails? to|insufficient to|unable to)\b",english_clause,re.I))
def strong_assertions(text):
    if text.endswith(('？','?')):return []
    return [m.group() for m in re.finditer(r'证明|排除|必然|唯一原因|唯一机制|直接鉴定|完全确定|\b(?:prove[sd]?|proven|proof|rules? out|excludes?|sole (?:cause|mechanism)|only (?:cause|mechanism)|directly identif(?:y|ies)|unambiguously establishes?)\b',text,re.I) if not negated(text,m.start())]
def initialize(inp,review):
    d=json.loads(Path(inp).read_text('utf-8'));r=json.loads(Path(review).read_text('utf-8'))
    return {'schema_version':1,'input_sha256':sha(inp),'review_sha256':sha(review),'comparisons':[], 'scopes':[], 'panels':[{'asset':fid,'panel':'','subject_state':'','metrics':[],'conditions':'','source_locator':'','pointers':[]} for fid in d['case'].get('figures',{})],'source_first_review':{'method':'','checked_claim_ids':[],'findings':[],'summary':''},'waivers':[]}
def validate(inp,review,context):
    d=json.loads(Path(inp).read_text('utf-8'));r=json.loads(Path(review).read_text('utf-8'));a=json.loads(Path(context).read_text('utf-8'));u=E.content_units(d);claims={c['id']:c for c in r['claims']};errors=[];warnings=[]
    profile=E.P.resolve(d['case']);materials_rules='materials_chemistry' in profile['disciplines']
    def err(x):errors.append(x)
    def text_ref(ref,where):
        if not isinstance(ref,dict) or ref.get('pointer') not in u or not ref.get('quote') or ref['quote'] not in u[ref['pointer']]:err(where+': qualification must quote current reader-visible text');return ''
        return ref['quote']
    if a.get('schema_version')!=1:err('context schema_version must be 1')
    if a.get('input_sha256')!=sha(inp) or a.get('review_sha256')!=sha(review):err('stale context audit; source-review and reader bytes must both match')
    waivers={w.get('pointer'):w for w in a.get('waivers',[]) if w.get('pointer') in u and w.get('text_sha256')==E.text_sha(u[w['pointer']]) and w.get('source_claim_id') in claims and len(w.get('source_reason',''))>=30}
    def flag(pointer,message):
        if pointer in waivers:warnings.append(message+'; explicit source-grounded exception retained at '+pointer)
        else:err(message+' at '+pointer)
    for c in a.get('comparisons',[]):
        groups=c.get('groups',[]);ptrs=c.get('pointers',[])
        if len(groups)<2 or not ptrs or any(p not in u for p in ptrs):err('comparison needs actual groups and reader pointers');continue
        keys=set().union(*(set(g.get('conditions',{})) for g in groups));different=[k for k in keys if len({str(g.get('conditions',{}).get(k,'unknown')).strip().casefold() for g in groups})>1]
        if not keys or any(not g.get('label') for g in groups):err('comparison groups require labels and conditions')
        kind=c.get('classification')
        if kind not in ['controlled','multi_condition','descriptive']:err('unknown comparison classification')
        if kind=='controlled' and any(str(g.get('conditions',{}).get(k,'unknown')).lower() in ['unknown','未知',''] for g in groups for k in keys):err('unknown comparison conditions cannot certify a controlled experiment')
        if len(different)>1:
            if kind=='controlled':err('multiple conditions differ but comparison is declared controlled: '+','.join(different))
            text_ref(c.get('qualification'), 'multi-condition comparison')
            for p in ptrs:
                for m in re.finditer(r'单变量|唯一差别|唯一不同|只改变|只相差|只差|\bsingle[- ]variable\b|\bonly (?:difference|change|variable)\b|\bdiffers? only\b|\bchanges? only\b',u[p],re.I):
                    if not negated(u[p],m.start()):flag(p,'multi-condition experiment described as isolated change')
        if not c.get('source_claim_ids') or any(i not in claims for i in c['source_claim_ids']):err('comparison lacks source-backed claim references')
    if not a.get('comparisons') and len(a.get('no_comparisons_reason',''))<30:err('record actual key comparisons, or explain why this paper has none')
    covered=set()
    for panel in a.get('panels',[]):
        fid=panel.get('asset');ptrs=panel.get('pointers',[])
        if fid not in d['case'].get('figures',{}):err('unknown panel asset');continue
        covered.add(fid)
        if any(not isinstance(panel.get(k),str) or not panel[k].strip() for k in ['panel','subject_state','conditions','source_locator']):err('panel map must identify actual panel, object/state, conditions and source: '+fid)
        if not isinstance(panel.get('metrics'),list) or not ptrs or any(p not in u for p in ptrs):err('panel map needs metrics list and visible explanation pointers: '+fid)
        # A panel explicitly declared G-prime only cannot be explained as measuring both moduli.
        metrics=' '.join(panel.get('metrics',[])).replace('′',"'").replace('″',"''")
        if materials_rules and "G'" in metrics and "G''" not in metrics:
            for p in ptrs:
                for match in re.finditer(r'G\s*[″]|G\s*\'\'|G[′\']\s*[/、与和]\s*G?[″]',u[p]):
                    if not negated(u[p],match.start()):flag(p,'panel metric map conflicts with explanation of both moduli')
    if covered!=set(d['case'].get('figures',{})):err('context panel map does not cover displayed figure evidence')
    for scope in a.get('scopes',[]):
        if scope.get('claim_id') not in claims or not scope.get('stage'):err('scope needs canonical claim and actual stage')
        text_ref(scope.get('visible_scope'), 'stage/scope qualification')
    review_state=a.get('source_first_review',{})
    if review_state.get('method') not in ['independent_agent','same_agent_second_pass'] or len(review_state.get('summary',''))<30:err('source-first context review is incomplete')
    if set(review_state.get('checked_claim_ids',[]))!=set(claims):err('source-first context pass must cover every canonical key claim')
    for f in review_state.get('findings',[]):
        if f.get('resolution') not in ['revised','retained_qualified']:err('unresolved review finding blocks final build: '+str(f.get('id')))
        text_ref(f.get('visible_resolution'),'review finding resolution')
        if not f.get('evidence_claim_ids') or any(i not in claims for i in f['evidence_claim_ids']):err('finding resolution lacks source evidence')
    for unit in r['units']:
        p=unit.get('pointer');t=u.get(p,'')
        if unit.get('kind')!='factual':continue
        linked=[claims[i] for i in unit.get('claim_ids',[]) if i in claims]
        formal_proved=bool(linked) and all(c['level']=='formal_result' and c.get('formal_status')=='proved_in_source' for c in linked)
        for m in re.finditer(r'排除|唯一原因|唯一机制|\b(?:rules? out|excludes?|sole (?:cause|mechanism)|only (?:cause|mechanism))\b',t,re.I):
            if not formal_proved and not negated(t,m.start()) and not t.endswith(('？','?')):flag(p,'categorical exclusion requires direct source-grounded justification, irrespective of assigned evidence level')
        if any(c['level'] in ['author_interpretation','model_result','author_claim','textual_interpretation'] for c in linked):
            if strong_assertions(t):flag(p,'interpretive evidence expressed as categorical proof/exclusion')
        if any(c['level']=='formal_result' and c.get('formal_status')!='proved_in_source' for c in linked) and strong_assertions(t):
            flag(p,'unproved formal claim expressed as established proof')
        if materials_rules and any(c['level'] in ['author_interpretation','model_result','author_claim'] for c in linked):
            inference=re.search(r'(?:这说明|表明|意味着|因此|从而|指向).{0,35}(?:链间|二硫键|共价|机理|机制|拥挤|拓扑)',t)
            if inference and not negated(t,inference.start()) and not re.search(r'作者|解释|支持|提示|提出|推测|假设|认为|模型|可能|不能|并未|不等于',t):flag(p,'inferential connection claim lacks visible attribution or qualification')
            en_inference=re.search(r'\b(?:this|these|the results?|the data)\s+(?:shows?|demonstrates?|means?|indicates?|implies?).{0,70}\b(?:interchain|disulfide|covalent|mechanism|topology)\b',t,re.I)
            if en_inference and not negated(t,en_inference.start()) and not re.search(r"\b(?:authors?|interpret\w*|support\w*|suggest\w*|propos\w*|hypothes\w*|models?|may|might|not|cannot)\b|consistent with",t,re.I):flag(p,'inferential connection claim lacks visible attribution or qualification')
        if not materials_rules:continue
        for m in re.finditer(r'(?:整个|全程|全部).{0,12}(?:无需|不需要|无引发剂|无金属)',t):
            if not negated(t,m.start()):flag(p,'stage-limited advantage expanded to entire process')
        for m in re.finditer(r'(?:NMR|核磁|谱峰|SEM|显微).{0,30}(?:证明|说明|直接鉴定).{0,25}(?:链间|二硫(?:键|交联)|连接拓扑|湿态网)',t):
            if not negated(t,m.start()) and not re.search(r'不能|并未|不等于|不足以|不是',m.group()) and not re.search(r'解释为|据此解释|作者认为|作者将|推测|支持',t):flag(p,'indirect measurement promoted to direct connection/topology proof')
        for m in re.finditer(r'\b(?:NMR|SEM|microscopy|spectral peaks?).{0,70}\b(?:proves?|directly identif(?:y|ies)|directly demonstrates?).{0,70}\b(?:interchain|disulfide (?:bonds?|crosslinks?)|topology|hydrated network)\b',t,re.I):
            if not negated(t,m.start()) and not re.search(r'\b(?:not|cannot|authors?|interpret\w*|support\w*|suggest\w*|may|might)\b',m.group(),re.I):flag(p,'indirect measurement promoted to direct connection/topology proof')
        for m in re.finditer(r'\b(?:entire|whole)\s+(?:synthe\w*|process|route).{0,55}\b(?:without|free of|no added)\b',t,re.I):
            if not negated(t,m.start()):flag(p,'stage-limited advantage expanded to entire process')
    encoding=V.check_text('\n'.join(u.values()),d['case'].get('language',V.DEFAULT_LANGUAGE));errors.extend(encoding['errors'])
    return {'passed':not errors,'errors':errors,'warnings':warnings,'input_sha256':sha(inp),'context_sha256':sha(context),'comparisons':len(a.get('comparisons',[])),'panels':len(a.get('panels',[])),'reading_profile':profile,'scientific_entailment_automatically_judged':False,'encoding':encoding}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('--review',required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--context');g.add_argument('--init');p.add_argument('--output');a=p.parse_args()
    try:result=initialize(a.input,a.review) if a.init else validate(a.input,a.review,a.context)
    except (ValueError,KeyError,OSError,TypeError) as e:result={'passed':False,'errors':[str(e)]}
    target=a.init or a.output
    if target:Path(target).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False));return 0 if a.init or result.get('passed') else 1
if __name__=='__main__':raise SystemExit(main())
