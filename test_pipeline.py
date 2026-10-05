import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bookwriter.core import (BASE, CITATION, FactChecker, Pipeline, Planner, Researcher,
                             SourceFetcher, mechanical_issues, safe_url, sentences)
from bookwriter.demo import FixtureClient, FixtureFetcher

CARDS = json.loads((BASE/'examples/source_cards.json').read_text())
SEEDS = [{k:s[k] for k in ['id','publisher','title','url']} for s in CARDS]
CHAPTER = json.loads((BASE/'examples/chapters.json').read_text())[0]

class AnswerClient:
    def __init__(self, answer): self.answer=answer
    def ask(self, *args): return self.answer

class WorkflowTests(unittest.TestCase):
    def test_demo_revises_and_writes_all_chapters(self):
        with tempfile.TemporaryDirectory() as tmp, patch('builtins.print'):
            out=Path(tmp)/'run'
            status=Pipeline(FixtureClient(),FixtureFetcher(CARDS),SEEDS,out,mode='demo').run()
            self.assertEqual(status['status'],'demo_complete')
            self.assertEqual(len(status['words']),3)
            self.assertTrue((out/'chapter-1-draft-1.json').exists())
            self.assertEqual((out/'book.md').read_text().count('### References'),3)
            self.assertIn('OFFLINE DEMO',(out/'book.html').read_text())
    def test_revision_limit_never_publishes(self):
        with tempfile.TemporaryDirectory() as tmp, patch('builtins.print'):
            out=Path(tmp)/'run'
            with self.assertRaises(RuntimeError):
                Pipeline(FixtureClient(),FixtureFetcher(CARDS),SEEDS,out,max_revisions=0,mode='demo').run()
            self.assertFalse((out/'book.md').exists())
            self.assertEqual(json.loads((out/'status.json').read_text())['status'],'failed')
    def test_unknown_reference_rejected(self):
        c=json.loads(json.dumps(CHAPTER)); c['paragraphs'][0]+=' A claim. [999]'
        self.assertTrue(any('Unknown citation' in x for x in mechanical_issues(c,range(1,6))))
    def test_uncited_date_rejected(self):
        c=json.loads(json.dumps(CHAPTER)); c['paragraphs'][0]+=' It began in 2017.'
        self.assertTrue(any('uncited number' in x for x in mechanical_issues(c,range(1,6))))
    def test_word_count_and_takeaway_rejected(self):
        c={'title':'Short','paragraphs':['Too short.'],'takeaway':'Conclusion'}
        issues=mechanical_issues(c,[1])
        self.assertTrue(any('words' in x for x in issues))
        self.assertTrue(any('Takeaway' in x for x in issues))
    def test_every_sentence_must_be_reviewed(self):
        with self.assertRaises(ValueError):
            FactChecker(AnswerClient({'checks':[]})).run(CHAPTER,CARDS)
    def test_duplicate_sentence_checks_rejected(self):
        result=FixtureClient().ask('Fact-checker','',{'sentences':list(enumerate(sentences(CHAPTER))),'sources':CARDS})
        result['checks'][-1]['sentence_index']=0
        with self.assertRaises(ValueError): FactChecker(AnswerClient(result)).run(CHAPTER,CARDS)
    def test_fabricated_evidence_rejected(self):
        result=FixtureClient().ask('Fact-checker','',{'sentences':list(enumerate(sentences(CHAPTER))),'sources':CARDS})
        cited=next(c for c in result['checks'] if c['supports'])
        cited['supports'][0]['quote']='A made up quotation that is not in the source.'
        issues,_=FactChecker(AnswerClient(result)).run(CHAPTER,CARDS)
        self.assertTrue(any('invalid evidence' in x for x in issues))
    def test_unsupported_fact_rejected(self):
        result=FixtureClient().ask('Fact-checker','',{'sentences':list(enumerate(sentences(CHAPTER))),'sources':CARDS})
        result['checks'][0].update(verdict='unsupported',reason='Uncited empirical assertion')
        issues,_=FactChecker(AnswerClient(result)).run(CHAPTER,CARDS)
        self.assertTrue(any('Uncited empirical' in x for x in issues))
    def test_cited_advice_cannot_skip_verification(self):
        result=FixtureClient().ask('Fact-checker','',{'sentences':list(enumerate(sentences(CHAPTER))),'sources':CARDS})
        next(c for c in result['checks'] if c['supports'])['verdict']='advice'
        issues,_=FactChecker(AnswerClient(result)).run(CHAPTER,CARDS)
        self.assertTrue(any('needs evidence review' in x for x in issues))
    def test_plan_requires_three_chapters(self):
        with self.assertRaises(ValueError): Planner(AnswerClient({'chapters':[]})).run({})
    def test_fetch_failures_have_no_cache_fallback(self):
        class Broken:
            def fetch(self,s): raise ValueError('Unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError): Researcher(FixtureClient(),Broken()).run({},SEEDS,Path(tmp),lambda *a:None)
    def test_private_http_and_unknown_hosts_rejected(self):
        for url in ['http://www.pib.gov.in/x','https://127.0.0.1/x','https://evil.example/x','https://user:pw@www.pib.gov.in/x','https://www.pib.gov.in:8000/x']:
            with self.assertRaises(ValueError): safe_url(url)
    def test_changed_source_blocks_release(self):
        class Changing(FixtureFetcher):
            def __init__(self,c): super().__init__(c); self.n=0
            def fetch(self,s):
                self.n+=1; value=super().fetch(s)
                if self.n>15: value['sha256']='changed'
                return value
        with tempfile.TemporaryDirectory() as tmp, patch('builtins.print'):
            out=Path(tmp)/'run'
            with self.assertRaises(RuntimeError): Pipeline(FixtureClient(),Changing(CARDS),SEEDS,out,mode='demo').run()
            self.assertFalse((out/'book.md').exists())
    def test_sentence_citations_stay_with_claim(self):
        c={'paragraphs':['UPI launched in 2016. [1] Here is advice.'], 'takeaway':'Takeaway: Practise.'}
        self.assertEqual(sentences(c)[0],'UPI launched in 2016. [1]')
        self.assertEqual(len(sentences(c)),3)
    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError): Pipeline(FixtureClient(),FixtureFetcher(CARDS),SEEDS,tmp,mode='demo').run()

if __name__=='__main__': unittest.main()
