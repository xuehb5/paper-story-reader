"""Check plan completeness and source anchors; this does not judge scientific validity."""
from pathlib import Path
import argparse
import json
import re
import unicodedata

def norm(value):
    return ' '.join(unicodedata.normalize('NFKC',value).split())

def validate_plan(plan,plan_file,case=None):
    base=Path(plan_file).resolve().parent;errors=[];checked=0;indexes={}
    def need(obj,key,where):
        if not isinstance(obj.get(key),str) or not obj[key].strip():errors.append(f'{where}: missing {key}')
    need(plan,'central_question','plan')
    contribution=plan.get('contribution',{})
    for field in ['prior_limit','new_move','bounded_claim']:need(contribution,field,'contribution')
    entities=plan.get('entity_states',[])
    if not entities or any(not e.get('object') or not e.get('states') for e in entities):errors.append('entity_states: objects and states required')
    route=plan.get('reading_route',[])
    if not route or len(route)!=len(set(route)):errors.append('reading_route: nonempty unique section ids required')
    if case and route!=[s['id'] for s in case['sections']]:errors.append('reading_route does not match reader sections')
    for sid,source in plan.get('sources',{}).items():
        file=base/source['text_file']
        if not file.exists():errors.append(f'source {sid}: missing {file.name}');continue
        index={}
        for line in file.read_text(encoding='utf-8').splitlines():
            anchor,sep,text=line.partition('\t')
            if sep and re.search(r'-P\d+-L\d+$',anchor):index[anchor]=text
        indexes[sid]=index
    nodes=plan.get('argument_nodes',[]);ids=set()
    if not nodes:errors.append('argument_nodes: empty')
    for node in nodes:
        ident=node.get('id','?')
        if ident in ids:errors.append(f'{ident}: duplicate argument id')
        ids.add(ident)
        for field in ['question','claim','test_or_comparison','what_it_does_not_establish','remaining_question']:need(node,field,ident)
        if node.get('inference_level') not in ['observation','design_rationale','author_interpretation','model_result','synthesis','derived','background','author_claim','formal_result','assumption','qualitative_finding','textual_interpretation']:errors.append(f'{ident}: invalid inference_level')
        if not node.get('story_sections') or any(s not in route for s in node.get('story_sections',[])):errors.append(f'{ident}: unknown story section')
        evidence=node.get('evidence',[])
        if not evidence:errors.append(f'{ident}: no evidence')
        for ev in evidence:
            index=indexes.get(ev.get('source'),{})
            start,end=ev.get('anchor_start',''),ev.get('anchor_end','')
            a,b=re.search(r'-P(\d+)-L(\d+)$',start),re.search(r'-P(\d+)-L(\d+)$',end)
            if not a or not b or a[1]!=b[1] or int(a[2])>int(b[2]) or int(a[1])!=ev.get('page') or start not in index or end not in index:
                errors.append(f'{ident}: invalid source range {start}..{end}');continue
            prefix=start.rsplit('-L',1)[0]
            anchors=[prefix+f'-L{i:03d}' for i in range(int(a[2]),int(b[2])+1)]
            if any(anchor not in index for anchor in anchors):errors.append(f'{ident}: incomplete source range');continue
            text=' '.join(index[anchor] for anchor in anchors)
            if not ev.get('excerpt') or norm(ev['excerpt']) not in norm(text):errors.append(f'{ident}: excerpt does not match source text')
            else:checked+=1
    pairs=[(t.get('from'),t.get('to')) for t in plan.get('transitions',[])]
    if pairs!=list(zip(route,route[1:])):errors.append('transitions do not follow the complete reading route')
    for transition in plan.get('transitions',[]):
        for field in ['resolved','still_unknown','why_next']:need(transition,field,'transition')
    questions=plan.get('reader_checks',[])
    if len(questions)<2:errors.append('reader_checks: need at least two source-backed questions')
    for question in questions:
        for field in ['question','expected_answer']:need(question,field,'reader check')
        if not question.get('argument_ids') or any(i not in ids for i in question.get('argument_ids',[])):errors.append('reader check references unknown argument')
    return {'passed':not errors,'argument_nodes':len(nodes),'evidence_ranges_checked':checked,'transitions':len(pairs),'reader_checks':len(questions),'scientific_sufficiency_automatically_judged':False,'errors':errors}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('plan');parser.add_argument('--case');parser.add_argument('--output');args=parser.parse_args()
    plan=Path(args.plan);result=validate_plan(json.loads(plan.read_text(encoding='utf-8')),plan,json.loads(Path(args.case).read_text(encoding='utf-8')) if args.case else None)
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:Path(args.output).write_text(text+'\n',encoding='utf-8')
    print(text);return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
