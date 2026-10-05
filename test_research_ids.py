import tempfile
import unittest
from pathlib import Path
from bookwriter.core import Researcher
from bookwriter.demo import FixtureFetcher

CARDS=[dict(id=i,publisher='Official',title='Source',url='https://www.pib.gov.in/x',text='UPI payments use real source evidence. '+str(i)) for i in [1,2]]
class Client:
    model_id='local-test'
    def __init__(self,invalid=False): self.invalid=invalid
    def ask(self,role,instruction,payload):
        return {'evidence':[{'evidence_id':999 if self.invalid else 1,'use':'Explains UPI','quote':'Invented model text must be ignored'}]}
class Tests(unittest.TestCase):
    def test_local_quote_copied_by_code(self):
        with tempfile.TemporaryDirectory() as t:
            sources,packet=Researcher(Client(),FixtureFetcher(CARDS)).run({'title':'UPI'},CARDS,Path(t),lambda *a:None)
            self.assertEqual(packet['evidence'][0]['quote'],CARDS[0]['text'])
    def test_unknown_id_still_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError): Researcher(Client(True),FixtureFetcher(CARDS)).run({'title':'UPI'},CARDS,Path(t),lambda *a:None)
if __name__=='__main__': unittest.main()
