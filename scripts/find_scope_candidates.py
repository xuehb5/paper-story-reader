"""Locate wording that deserves a source-scope check. This is not a scientific verifier."""
from pathlib import Path
import argparse,hashlib,json,re

PATTERNS={
 'exclusive_comparison':re.compile(r'只(?:差|改|有|改变)|仅(?:差|有|改变|由)|唯一|\b(?:only|solely)\b',re.I),
 'extended_scope':re.compile(r'全部|所有|整个|均(?=为|是|有|可|能|不|在)|都(?:是|能|可|不|已)|\b(?:all|entire|fully)\b',re.I),
 'evidence_strength':re.compile(r'证明|排除|必然|直接(?:表明|揭示|确定)|\b(?:prove[sd]?|exclude[sd]?)\b',re.I),
}
SKIP={'id','doi','citation','paper_title','audience','refs','source_ids','source','target','from','to','href','kind','side','parent','claim_id'}

def locate(data):
 rows=[]
 def walk(value,pointer):
  if isinstance(value,dict):
   for k,v in value.items():
    if k not in SKIP:walk(v,pointer+'/'+k.replace('~','~0').replace('/','~1'))
  elif isinstance(value,list):
   for i,v in enumerate(value):walk(v,pointer+'/'+str(i))
  elif isinstance(value,str):
   hits={name:sorted(set(m.group() for m in pattern.finditer(value))) for name,pattern in PATTERNS.items() if pattern.search(value)}
   if hits:rows.append({'pointer':pointer,'text_sha256':hashlib.sha256(value.encode()).hexdigest(),'text':value,'hints':hits,'scientific_status':'not_judged'})
 walk(data.get('case',{}),'/case')
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('--out');a=p.parse_args();source=Path(a.input);raw=source.read_bytes();data=json.loads(raw.decode('utf-8-sig'))
 result={'schema_version':1,'input_sha256':hashlib.sha256(raw).hexdigest(),'purpose':'navigation hints for a source-context audit, not a pass/fail gate','limitations':['Lexical hints have false positives and omissions.','No scientific entailment, figure reading, condition extraction or quality score is computed.','Zero candidates does not mean a correct or fully reviewed reader.'],'candidates':locate(data)}
 body=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
 if a.out:Path(a.out).write_text(body,'utf-8')
 else:print(body,end='')
if __name__=='__main__':main()
