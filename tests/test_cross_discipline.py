"""Mechanical contracts on explicitly synthetic sources; these are not paper-quality evaluations."""
from pathlib import Path
import copy,importlib.util,json,re,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location('cross_test_'+name,ROOT/'scripts'/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
R=load('render_reader');E=load('validate_evidence');C=load('validate_release')

class CrossDisciplineContracts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        quote='For x = 0, x squared equals zero by multiplication.'
        self.claim={'id':'C1','statement':quote,'level':'formal_result','formal_status':'proved_in_source',
                    'assumptions':['x equals zero'],'subject':'the defined scalar x','conditions':'x = 0',
                    'scope':'this synthetic arithmetic example','support':'the explicit calculation in the source',
                    'limit':'not an empirical performance claim','evidence':[{'kind':'text','source':'main','locator':'synthetic source, first line','quote':quote}]}
        self.data={'case':{'id':'S','short':'Synthetic example','title':'A synthetic reading contract','category':'Synthetic fixture',
          'paper_title':'Synthetic source created for software verification','citation':'PaperStory maintainers; synthetic test fixture, not a published study.',
          'thesis':quote,'audience':'A software tester.','coverage':'Synthetic content only; no scientific reading-quality claim.',
          'language':'en','source_ids':['main'],'figures':{},
          'reading_profile':{'study_types':['theoretical'],'disciplines':['mathematics'],'rationale':'The source explicitly defines a scalar and supplies a direct arithmetic derivation.'},
          'materials':[{'id':'main-file','role':'main','status':'available','source':'main','note':'Synthetic local UTF-8 source.'}],
          'sections':[{'id':'reason','title':'Follow the definition','refs':['Synthetic source, first line'],'blocks':[quote,
           {'table':{'id':'values','label':'Table 1','title':'Defined values','source':'main','locator':'Synthetic source','columns':['x','x squared'],'rows':[['0','0']],'caption':'The defined example only.'}},
           {'detail':{'title':'Read the expression','kind':'explanation','side':'right','paragraphs':['The defined input is zero.'],'blocks':[
            {'equation':{'id':'square','label':'Equation 1','title':'Read the multiplication','source':'main','locator':'Synthetic source','expression':'0 × 0 = 0','variables':[{'symbol':'0','meaning':'The defined scalar value.'}],'explanation':'Multiplication of the defined value.','mathml':'<math xmlns="http://www.w3.org/1998/Math/MathML"><mrow><mn>0</mn><mo>×</mo><mn>0</mn><mo>=</mo><mn>0</mn></mrow></math>'}},
            {'quotation':{'id':'passage','label':'Original passage','title':'The exact source statement','source':'main','locator':'Synthetic source, first line','text':quote,'explanation':'The statement is quoted in its synthetic context.'}}]}}]}],
          'research_graph':{'nodes':[{'id':'claim','title':'Defined result','role':'Formal result','target':'reason-p1','finding':quote,'row':0,'column':'center','claim_id':'C1'}],'edges':[]}},'sources':{},'assets':{}}
        self.source=self.root/'source.txt';self.source.write_text(quote+'\n'+'\n'.join(E.content_units(self.data).values()),encoding='utf-8')
        self.data['sources']={'main':{'file':'source.txt','sha256':E.sha(self.source),'format':'text','description':'Explicitly synthetic local text source.'}}

    def tearDown(self):self.temp.cleanup()
    def files(self):
        inp=self.root/'input.json';inp.write_text(json.dumps(self.data,ensure_ascii=False),'utf-8')
        review=E.initialize(inp);review['claims']=[self.claim]
        for unit in review['units']:unit.update(kind='factual',claim_ids=['C1'],verdict='aligned',reason='Mechanical synthetic fixture; strings and structure are generated from its declared source, not a real-paper review.')
        review['reviewer']={'method':'same_agent_second_pass','identity':'synthetic fixture generator','source_first_summary':'Mechanical fixture only; no source-reading quality or independent scientific verification is claimed.','unresolved_items':[]}
        rev=self.root/'review.json';rev.write_text(json.dumps(review),'utf-8')
        context={'schema_version':1,'input_sha256':E.sha(inp),'review_sha256':E.sha(rev),'comparisons':[],
                 'no_comparisons_reason':'This explicitly synthetic arithmetic source has no empirical comparison or experimental groups.',
                 'panels':[],'scopes':[],'source_first_review':{'method':'same_agent_second_pass','checked_claim_ids':['C1'],'summary':'Synthetic source and generated contract checked for mechanical software testing only.','findings':[]}}
        ctx=self.root/'context.json';ctx.write_text(json.dumps(context),'utf-8')
        return inp,rev,ctx

    def test_reviewed_non_doi_reader_has_all_evidence_and_shared_navigation(self):
        inp,rev,ctx=self.files();out=self.root/'reader'
        report=R.build(inp,out,rev,False,ctx)
        self.assertEqual(report['rich_evidence_blocks'],3)
        self.assertEqual(report['figures'],0)
        self.assertEqual(report['question_branches'],1)
        html=(out/'S.html').read_text('utf-8')
        self.assertIn('Research stories · Offline companion',html)
        self.assertIn('Evidence index · By research question',html)
        for target in ('values','square','passage'):
            self.assertIn('id="evidence-'+target+'"',html)
            self.assertIn('href="#evidence-'+target+'"',html)
        self.assertIn('<math xmlns=',html)
        self.assertIn('sources/',html)
        self.assertNotIn('https://doi.org/None',html)
        self.assertEqual(len(re.findall('class="paper-world"',html)),1)

    def test_each_table_cell_and_equation_definition_requires_current_review(self):
        inp,rev,ctx=self.files();review=json.loads(rev.read_text('utf-8'))
        pointer='/case/sections/0/blocks/1/table/rows/0/1'
        self.assertIn(pointer,{u['pointer'] for u in review['units']})
        self.data['case']['sections'][0]['blocks'][1]['table']['rows'][0][1]='1'
        inp.write_text(json.dumps(self.data),'utf-8')
        result=E.validate_review(inp,rev)
        self.assertFalse(result['passed']);self.assertTrue(any('changed/unreviewed' in e for e in result['errors']))

    def test_ragged_table_is_rejected(self):
        self.data['case']['sections'][0]['blocks'][1]['table']['rows']=[['0']]
        inp,rev,ctx=self.files()
        with self.assertRaisesRegex(ValueError,'rectangular'):R.build(inp,self.root/'draft',draft=True)

    def test_active_math_markup_is_rejected(self):
        value=self.data['case']['sections'][0]['blocks'][2]['detail']['blocks'][0]['equation']
        value['mathml']='<math><mtext onclick="alert(1)">x</mtext></math>'
        inp,_,_=self.files()
        with self.assertRaisesRegex(ValueError,'MathML attribute'):R.build(inp,self.root/'draft',draft=True)

    def test_a_quotation_cannot_be_replaced_by_an_invented_passage(self):
        self.data['case']['sections'][0]['blocks'][2]['detail']['blocks'][1]['quotation']['text']='An invented claim not present in the original evidence.'
        inp,rev,_=self.files();result=E.validate_review(inp,rev)
        self.assertFalse(result['passed']);self.assertTrue(any('quotation must exactly match' in e for e in result['errors']))

    def test_formal_result_needs_theoretical_route_and_actual_assumptions(self):
        self.data['case']['reading_profile']['study_types']=['computational'];self.claim['assumptions']=[]
        inp,rev,_=self.files();result=E.validate_review(inp,rev)
        self.assertFalse(result['passed'])
        self.assertTrue(any('requires a theoretical' in e for e in result['errors']))
        self.assertTrue(any('actual formal assumptions' in e for e in result['errors']))

    def test_a_conjecture_cannot_be_described_as_a_proof(self):
        self.claim['formal_status']='conjecture';self.data['case']['thesis']='The proof establishes the result.'
        inp,rev,ctx=self.files();result=C.validate(inp,rev,ctx)
        self.assertFalse(result['passed']);self.assertTrue(any('unproved formal claim' in e for e in result['errors']))

    def test_formal_proof_language_remains_available_for_source_proved_results(self):
        self.data['case']['thesis']='The proof excludes nonzero values under the stated assumption.'
        inp,rev,ctx=self.files();result=C.validate(inp,rev,ctx)
        self.assertTrue(result['passed'],result['errors'])

    def test_non_pdf_sources_cannot_invent_physical_pages(self):
        self.data['case']['sections'][0]['blocks'][1]['table']['page']=1
        inp,_,_=self.files()
        with self.assertRaisesRegex(ValueError,'do not assign PDF'):R.build(inp,self.root/'draft',draft=True)

    def test_missing_si_and_unpublished_si_are_distinct(self):
        self.data['case']['materials'].append({'id':'si','role':'supplement','status':'not_provided','note':'The user has not supplied the known matching attachment.'})
        inp,rev,_=self.files();self.assertTrue(E.validate_review(inp,rev)['passed'])
        self.data['case']['materials'][-1]['status']='not_published'
        inp,rev,_=self.files();result=E.validate_review(inp,rev)
        self.assertFalse(result['passed']);self.assertTrue(any('source basis' in e for e in result['errors']))

    def test_incorrect_route_fails(self):
        self.data['case']['reading_profile']['study_types']=['anything']
        inp,_,_=self.files()
        with self.assertRaisesRegex(ValueError,'supported study_types'):R.build(inp,self.root/'draft',draft=True)

    def test_unknown_argument_relation_fails(self):
        self.data['case']['research_graph']['edges']=[{'from':'claim','to':'claim','kind':'proves_everything','label':'Unsupported relationship'}]
        inp,_,_=self.files()
        with self.assertRaisesRegex(ValueError,'relationship'):R.build(inp,self.root/'draft',draft=True)

    def test_profile_does_not_remove_source_hash_checks(self):
        inp,rev,_=self.files();self.source.write_text('Changed original source.','utf-8')
        result=E.validate_review(inp,rev)
        self.assertFalse(result['passed']);self.assertTrue(any('source missing or hash changed' in e for e in result['errors']))

if __name__=='__main__':unittest.main()
