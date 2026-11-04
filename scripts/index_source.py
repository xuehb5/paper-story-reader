"""Index a supplied PDF or JATS source with stable evidence anchors; optionally render PDF pages."""
import argparse, hashlib, json, logging, re, xml.etree.ElementTree as ET
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('--id',required=True);p.add_argument('--output',required=True);p.add_argument('--render-pages',default='');a=p.parse_args()
 if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',a.id):p.error('invalid source id')
 source=Path(a.source).resolve();out=Path(a.output).resolve();raw=source.read_bytes();figures=[];doi=None
 if raw.startswith(b'%PDF'):
  try:from pypdf import PdfReader
  except ImportError:p.error('PDF indexing requires pypdf in the current Python; use an available PDF tool instead if unavailable')
  out.mkdir(parents=True,exist_ok=True)
  log=logging.getLogger('pypdf');log.handlers=[logging.FileHandler(out/(a.id+'-pdf-warnings.log'),encoding='utf-8')];log.propagate=False
  doc=PdfReader(source);pages=[page.extract_text(extraction_mode='layout') or '' for page in doc.pages];fmt='pdf';description='PDF物理页码；解析警告另存日志，须结合原页核对'
 elif source.suffix.lower()=='.xml':
  root=ET.fromstring(raw);body=root.find('body')
  if body is None:p.error('JATS body missing')
  doi=next((e.text for e in root.findall('.//article-id') if e.get('pub-id-type')=='doi'),None)
  pages=['\n'.join(re.sub(r'<svg\b.*?</svg>','[公式或键型见原图]',' '.join(''.join(e.itertext()).split()),flags=re.S) for e in body.iter() if e.tag in ['article-title','title','p','table-wrap'])]
  for fig in root.findall('.//fig'):
   figures.append({'id':fig.get('id'),'label':''.join(fig.findtext('label') or ''),'caption':' '.join(''.join(fig.find('caption').itertext()).split()) if fig.find('caption') is not None else '', 'images':[e.get('{http://www.w3.org/1999/xlink}href') for e in fig.findall('graphic')]})
  fmt='jats';description='JATS逻辑文本页P001；非PDF物理页。来源位置用图号及段落锚点。'
 else:p.error('expected selectable PDF or JATS XML')
 if not any(t.strip() for t in pages):p.error('no text extracted; OCR may be needed; no empty successful index written')
 requested=[int(n) for n in a.render_pages.split(',') if n.strip()]
 if requested and fmt!='pdf':p.error('JATS has no PDF pages; view supplied original figures instead')
 if any(n<1 or n>len(pages) for n in requested):p.error('render page outside PDF')
 out.mkdir(parents=True,exist_ok=True)
 lines=[f'{a.id}-P{page:03d}-L{line:03d}\t{text}' for page,content in enumerate(pages,1) for line,text in enumerate(content.splitlines(),1)]
 textfile=out/(a.id+'.txt');textfile.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 if requested:
  try:import pypdfium2
  except ImportError:p.error('rendering needs pypdfium2; use an available PDF renderer instead')
  document=pypdfium2.PdfDocument(source)
  for n in requested:document[n-1].render(scale=1.7).to_pil().convert('RGB').save(out/f'{a.id}-p{n}.jpg',quality=92)
 record={'id':a.id,'file':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'format':fmt,'pages':len(pages) if fmt=='pdf' else None,'description':description,'doi':doi,'text_file':textfile.name,'lines':len(lines),'figures':figures,'rendered_pages':requested}
 (out/(a.id+'.source.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in record.items() if k!='figures'},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
