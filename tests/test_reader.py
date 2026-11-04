"""Observable reader, evidence and portable-delivery contracts."""
from pathlib import Path
import copy,importlib.util,json,shutil,subprocess,sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=ROOT/'examples/hydrogel'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

renderer=load('reader_under_test',ROOT/'scripts/render_reader.py')
delivery=load('delivery_under_test',ROOT/'scripts/verify_delivery.py')
release=load('release_under_test',ROOT/'scripts/validate_release.py')

class ReaderContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def build(self,out=None,**kw):
        return renderer.build(EXAMPLE/'reader-input.json',out or self.root/'reader',EXAMPLE/'evidence-review.json',False,EXAMPLE/'context-audit.json',**kw)
    def test_reviewed_example_builds_offline_and_verifies(self):
        out=self.root/'reader';report=self.build(out)
        self.assertTrue(report['source_review']['passed'])
        self.assertTrue(report['context_review']['passed'])
        self.assertEqual(report['sections'],7)
        self.assertEqual(report['figures'],25)
        self.assertGreater(report['optional_panel_explanations'],0)
        self.assertGreater(report['composites'],0)
        self.assertTrue(report['all_navigation_targets_valid'])
        self.assertTrue(delivery.verify([out/'A.html',out/'A.md'],manifest=out/'delivery-manifest.json')['passed'])
        html=(out/'A.html').read_text('utf-8')
        self.assertIn('paper-viewport',html)
        self.assertIn('研究论证',html)
        self.assertNotIn('<script src="http',html)
    def test_post_build_tampering_is_detected(self):
        out=self.root/'reader';self.build(out)
        p=out/'A.md';p.write_text(p.read_text('utf-8')+'\nchanged\n','utf-8')
        self.assertFalse(delivery.verify([p],manifest=out/'delivery-manifest.json')['passed'])
    def test_missing_review_cannot_be_published_as_reviewed(self):
        with self.assertRaisesRegex(ValueError,'source review required'):
            renderer.build(EXAMPLE/'reader-input.json',self.root/'reader',self.root/'absent.json')
    def context_with_caption(self,caption):
        data=json.loads((EXAMPLE/'reader-input.json').read_text('utf-8'))
        review=json.loads((EXAMPLE/'evidence-review.json').read_text('utf-8'))
        context=json.loads((EXAMPLE/'context-audit.json').read_text('utf-8'))
        data['case']['figures']['hybrid-i']['caption']=caption
        unit=next(u for u in review['units'] if u['pointer']=='/case/figures/hybrid-i/caption')
        unit['text_sha256']=release.E.text_sha(caption)
        inp=self.root/'input.json';inp.write_text(json.dumps(data,ensure_ascii=False),'utf-8')
        review['input_sha256']=release.sha(inp)
        rev=self.root/'review.json';rev.write_text(json.dumps(review,ensure_ascii=False),'utf-8')
        context['input_sha256']=release.sha(inp);context['review_sha256']=release.sha(rev)
        ctx=self.root/'context.json';ctx.write_text(json.dumps(context,ensure_ascii=False),'utf-8')
        return release.validate(inp,rev,ctx)
    def test_gprime_only_panel_accepts_explicit_missing_gdoubleprime(self):
        result=self.context_with_caption('两种符号对应两个体系的G′；没有G″曲线。')
        self.assertTrue(result['passed'],result['errors'])
    def test_gprime_only_panel_rejects_invented_second_modulus(self):
        result=self.context_with_caption('两种符号同时给出G′和G″曲线。')
        self.assertTrue(any('panel metric map conflicts' in e for e in result['errors']))
    def test_explicit_draft_is_visibly_marked(self):
        out=self.root/'draft';r=renderer.build(EXAMPLE/'reader-input.json',out,draft=True)
        self.assertEqual(r['content_review_status'],'draft_unreviewed')
        self.assertIn('草稿：来源核查尚未完成',(out/'A.html').read_text('utf-8'))
    def test_nonempty_output_is_preserved(self):
        out=self.root/'reader';out.mkdir();(out/'my-notes.txt').write_text('keep','utf-8')
        with self.assertRaisesRegex(ValueError,'output directory must be empty'):self.build(out)
        self.assertEqual((out/'my-notes.txt').read_text('utf-8'),'keep')
    def test_changed_source_bytes_block_rendering(self):
        work=self.root/'example';shutil.copytree(EXAMPLE,work)
        src=work/'sources/article.xml';src.write_bytes(src.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'source missing or hash changed'):
            renderer.build(work/'reader-input.json',self.root/'reader',work/'evidence-review.json',context_file=work/'context-audit.json')
    def test_changed_prose_invalidates_existing_review(self):
        work=self.root/'example';shutil.copytree(EXAMPLE,work)
        p=work/'reader-input.json';d=json.loads(p.read_text('utf-8'));d['case']['thesis']+=' This is a new claim.';p.write_text(json.dumps(d,ensure_ascii=False),'utf-8')
        with self.assertRaisesRegex(ValueError,'review is stale'):
            renderer.build(p,self.root/'reader',work/'evidence-review.json',context_file=work/'context-audit.json')
    def test_source_index_preserves_real_doi(self):
        out=self.root/'index'
        r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/index_source.py'),str(EXAMPLE/'sources/article.xml'),'--id','paper-main','--output',str(out)],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(r.returncode,0,r.stderr)
        data=json.loads((out/'paper-main.source.json').read_text('utf-8'))
        self.assertEqual(json.loads(r.stdout)['doi'].lower(),'10.1039/d4sc08284b')
        self.assertEqual(data['doi'].lower(),'10.1039/d4sc08284b')
        self.assertGreater(data['lines'],0)

if __name__=='__main__':unittest.main()
