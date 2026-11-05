"""Package an English or Chinese PaperStory edition from the shared maintenance source."""
from pathlib import Path
import argparse,hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.21.0'

def package(output,language='en'):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('archive already exists; preserve it and choose a new path')
    files={}
    for name in ['LICENSE','requirements.txt','THIRD_PARTY_NOTICES.md']:
        files[name]=(ROOT/name).read_bytes()
    for directory in ['scripts','assets']:
        for p in (ROOT/directory).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.name!='package_skill.py':files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    if language=='en':
        files['SKILL.md']=(ROOT/'editions/en/SKILL.md').read_text('utf-8').replace('../../references/en/','references/').encode('utf-8')
        files['agents/openai.yaml']=(ROOT/'editions/en/agents/openai.yaml').read_bytes()
        for p in (ROOT/'references/en').glob('*.md'):files['references/'+p.name]=p.read_bytes()
    elif language=='zh':
        files['SKILL.md']=(ROOT/'SKILL.md').read_bytes();files['agents/openai.yaml']=(ROOT/'agents/openai.yaml').read_bytes()
        for directory in ['references','editions']:
            for p in (ROOT/directory).rglob('*'):
                if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    else:raise ValueError('language must be en or zh')
    files['reader-defaults.json']=(json.dumps({'language':language})+'\n').encode('utf-8')
    readme=('PaperStory '+VERSION+' — English edition\n\nImport the complete paper-story-reader folder into an Agent that supports local SKILL.md, files, images and Python. Retain scripts, assets, references and agents. Python 3.10+ is needed for rendering; install requirements.txt in a virtual environment for PDF text checks. This edition writes English directly and defaults the reader UI to English. Explicit case.language takes precedence. The package contains no model or scientific example. Full sources, examples and validation: https://github.com/xuehb5/paper-story-reader\n' if language=='en' else 'PaperStory '+VERSION+'｜中文入口\n\n将完整paper-story-reader文件夹导入支持本地SKILL.md的Agent，保留scripts、assets、references和agents。Python 3.10+用于生成，PDF核查依赖见requirements.txt。默认中文，case.language可显式选择en。完整示例与验证：https://github.com/xuehb5/paper-story-reader\n')
    files['README.md']=readme.encode('utf-8')
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):z.writestr('paper-story-reader/'+name,data)
    with zipfile.ZipFile(output) as z:
        if z.testzip():raise ValueError('archive integrity check failed')
    return {'file':str(output),'version':VERSION,'language':language,'files':len(files),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--language',choices=['en','zh'],default='en');p.add_argument('--output',required=True);a=p.parse_args()
    try:print(json.dumps(package(a.output,a.language),ensure_ascii=False));return 0
    except (OSError,ValueError) as e:print(json.dumps({'passed':False,'error':str(e)}));return 1
if __name__=='__main__':raise SystemExit(main())
