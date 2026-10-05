import unittest
from unittest.mock import patch
from bookwriter.paragraph_writer import render_sentences, write_in_parts
from bookwriter.local import LocalClient
from bookwriter.core import mechanical_issues

class Tests(unittest.TestCase):
    def test_unknown_citation_id_is_rejected(self):
        with self.assertRaises(ValueError): render_sentences([{'text':'A claim.','source_ids':[9]}],{1})
    def test_citation_ids_are_rendered_next_to_sentence(self):
        self.assertEqual(render_sentences([{'text':'A claim.','source_ids':[1]},{'text':'Consider practising.','source_ids':[]}],{1}), 'A claim. [1] Consider practising.')
    def test_short_paragraph_stops_after_two_attempts(self):
        with patch('bookwriter.paragraph_writer.generate_prose', return_value='Too short.') as generate:
            with self.assertRaises(RuntimeError): write_in_parts(object(),{'title':'UPI'},{'evidence':[{'source_id':1}]})
            self.assertEqual(generate.call_count,2)
    def test_fact_review_quote_is_copied_from_original(self):
        client=LocalClient.__new__(LocalClient)
        quote='This original source explains the UPI payment system.'
        client._ask_one=lambda *a: {'checks':[{'sentence_index':0,'verdict':'supported','supports':[1]}]}
        result=client.ask('Fact-checker','',{'sentences':[(0,'A claim. [1]')],'sources':[{'id':1,'text':quote}]})
        self.assertEqual(result['checks'][0]['supports'],[{'source_id':1,'quote':quote}])
    def test_fact_review_unknown_evidence_id_rejected(self):
        client=LocalClient.__new__(LocalClient)
        client._ask_one=lambda *a: {'checks':[{'sentence_index':0,'verdict':'supported','supports':[99]}]}
        with self.assertRaises(ValueError): client.ask('Fact-checker','',{'sentences':[(0,'A claim. [1]')],'sources':[{'id':1,'text':'Original source passage explaining a fact.'}]})

if __name__=='__main__': unittest.main()

class ChapterBudgetTests(unittest.TestCase):
    def test_shorter_paragraphs_build_to_required_total(self):
        # Individual 60-word pieces are allowed, but publication still needs full chapter length.
        paragraph=' '.join(['Consider']+['practising']*58+['carefully.'])+' [1]'
        with patch('bookwriter.paragraph_writer.generate_prose',return_value=paragraph):
            chapter=write_in_parts(object(),{'title':'UPI'},{'evidence':[{'source_id':1}]})
        self.assertEqual(mechanical_issues(chapter,[1]),[])
        self.assertGreater(len(chapter['paragraphs']),9)
