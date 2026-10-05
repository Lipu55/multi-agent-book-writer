import unittest
from unittest.mock import patch
from bookwriter.local import compact_payload, source_excerpt, parse_json, LocalClient

class LocalTests(unittest.TestCase):
    def test_extract_keeps_original_text(self):
        text='navigation '*300+' UPI PIN must not be shared with anyone. '+'footer '*300
        excerpt=source_excerpt(text,'UPI PIN shared',1200)
        self.assertIn('UPI PIN must not be shared with anyone.',excerpt)
        for part in excerpt.split('\n[excerpt gap]\n'): self.assertIn(part,text)
    def test_source_size_is_bounded(self):
        self.assertLess(len(source_excerpt('abc '*20000,'abc',1800)),2000)
    def test_short_source_not_changed(self):
        self.assertEqual(source_excerpt('UPI evidence','UPI'),'UPI evidence')
    def test_editor_does_not_receive_old_full_source_pages(self):
        value=compact_payload({'previous_chapters':[{'chapter':{'title':'x'},'sources':[{'text':'huge'}]}]})
        self.assertEqual(value['previous_chapters'],[{'title':'x'}])
    def test_json_fences_and_leading_commentary(self):
        self.assertEqual(parse_json('```json\n{"approved":true}\n```'),{'approved':True})
        self.assertEqual(parse_json('Response: {"issues":[]}'),{'issues':[]})
    def test_truncated_json_rejected(self):
        with self.assertRaises(ValueError): parse_json('{"checks":[')
    def test_fact_batches_preserve_indices(self):
        client=LocalClient.__new__(LocalClient)
        calls=[]
        def fake(role,instruction,payload,budget):
            calls.append(payload)
            return {'checks':[{'sentence_index':i} for i,s in payload['sentences']]}
        client._ask_one=fake
        result=client.ask('Fact-checker','',{'sentences':[(i,'Advice.') for i in range(13)],'sources':[]})
        self.assertEqual(len(calls),3)
        self.assertEqual([c['sentence_index'] for c in result['checks']],list(range(13)))
    def test_compacting_does_not_mutate_original(self):
        original={'sources':[{'id':1,'publisher':'P','title':'T','url':'U','text':'x '*5000}]}
        value=compact_payload(original)
        self.assertEqual(len(original['sources'][0]['text']),10000)
        self.assertLess(len(value['sources'][0]['text']),2000)

if __name__=='__main__': unittest.main()
