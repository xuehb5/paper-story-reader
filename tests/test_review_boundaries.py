"""Review coverage must not be bypassed by labels or a quote from another section."""
import copy,json,tempfile,unittest
from pathlib import Path
from test_cross_discipline import CrossDisciplineContracts,E

class ReviewBoundaries(unittest.TestCase):
    # Reuse a source-complete synthetic fixture; test only the new failure paths here.
    setUp=CrossDisciplineContracts.setUp
    tearDown=CrossDisciplineContracts.tearDown
    files=CrossDisciplineContracts.files
    def test_scientific_prose_cannot_be_marked_navigation(self):
        inp,rev,_=self.files();review=json.loads(rev.read_text('utf-8'))
        next(u for u in review['units'] if u['pointer']=='/case/thesis').update(kind='navigation',claim_ids=[])
        rev.write_text(json.dumps(review),'utf-8')
        result=E.validate_review(inp,rev)
        self.assertFalse(result['passed']);self.assertTrue(any('scientific text cannot bypass' in e for e in result['errors']))

    def test_jats_quote_must_belong_to_declared_anchor(self):
        original=self.claim['statement'];self.source.write_text('<article><body><sec id="definitions"><p>Only definitions occur in this section.</p></sec><sec id="calculation"><p>'+original+'</p></sec></body></article>','utf-8')
        self.data['sources']['main'].update(format='jats',sha256=E.sha(self.source))
        self.claim['evidence'][0]['anchor']='definitions'
        inp,rev,_=self.files();result=E.validate_review(inp,rev)
        self.assertFalse(result['passed']);self.assertTrue(any('declared source anchor' in e for e in result['errors']))

    def test_valid_jats_anchor_is_accepted(self):
        original=self.claim['statement'];self.source.write_text('<article><body><sec id="calculation"><p>'+original+'</p></sec></body></article>','utf-8')
        self.data['sources']['main'].update(format='jats',sha256=E.sha(self.source))
        self.claim['evidence'][0]['anchor']='calculation'
        inp,rev,_=self.files();self.assertTrue(E.validate_review(inp,rev)['passed'])

    def test_unknown_jats_anchor_is_rejected(self):
        original=self.claim['statement'];self.source.write_text('<article><body><sec id="calculation"><p>'+original+'</p></sec></body></article>','utf-8')
        self.data['sources']['main'].update(format='jats',sha256=E.sha(self.source))
        self.claim['evidence'][0]['anchor']='missing'
        inp,rev,_=self.files();result=E.validate_review(inp,rev)
        self.assertFalse(result['passed']);self.assertTrue(any('declared source anchor' in e for e in result['errors']))

del CrossDisciplineContracts

if __name__=='__main__':unittest.main()
