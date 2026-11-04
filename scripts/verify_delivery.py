"""Check decoded reader text and frozen delivery bytes; does not judge scientific meaning."""
import argparse,hashlib,json,re
from pathlib import Path
from html.parser import HTMLParser
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Visible(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.skip=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ['script','style']:self.skip+=1
    def handle_endtag(self,tag):
        if tag in ['script','style']:self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
def check_text(text,language='zh'):
    problems=[];han=len(re.findall('[\u3400-\u9fff]',text));questions=text.count('?')
    if '\ufffd' in text:problems.append('Unicode replacement character in delivered text')
    if re.search(r'\?{4,}',text) or (len(text)>100 and questions/max(1,len(text))>.04):problems.append('probable lossy text transfer: repeated question-mark replacements')
    if language=='zh' and len(text)>300 and han<20:problems.append('Chinese delivery requested but decoded reader text has too little Chinese')
    return {'passed':not problems,'characters':len(text),'han_characters':han,'question_marks':questions,'errors':problems}
def verify(files,language='zh',manifest=None):
    rows=[];errors=[]
    for name in files:
        p=Path(name);text=p.read_text('utf-8',errors='strict')
        if p.suffix.lower()=='.html':v=Visible();v.feed(text);text=' '.join(v.parts)
        row={'file':str(p),'sha256':sha(p),**check_text(text,language)};rows.append(row);errors.extend(row['errors'])
    if manifest:
        p=Path(manifest);data=json.loads(p.read_text('utf-8'))
        for rel,h in data['files'].items():
            target=(p.parent/rel).resolve()
            if not target.is_relative_to(p.parent.resolve()) or not target.is_file() or sha(target)!=h:errors.append('post-build output changed or absent: '+rel)
    return {'passed':not errors,'checks':rows,'errors':errors,'scientific_correctness_judged':False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('files',nargs='+');p.add_argument('--language',choices=['zh','en'],default='zh');p.add_argument('--manifest');p.add_argument('--output');a=p.parse_args()
    try:r=verify(a.files,a.language,a.manifest)
    except (OSError,ValueError,KeyError) as e:r={'passed':False,'errors':[str(e)]}
    if a.output:Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(r,ensure_ascii=False));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
