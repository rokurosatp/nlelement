import unittest
from nlelement import nlelement, cabocha_extended
from nlelement.testutil import testsamplemaker


class CabochaExtendedTest(unittest.TestCase):
    """cabocha_extendedのテキスト化, オブジェクト化の処理が正しく行われているかのテスト
    """
    def setUp(self):
        self.samples = testsamplemaker.NlElementSampleMaker()
    
    @unittest.skip("諸事情でsample3_argumentsがどこかに消えた")
    def test_mem_text_mem(self):
        doc = self.samples.sample3_arguments()
        dump = cabocha_extended.dump(doc)
        #with open('dat/log/cabocha_test.txt', 'w', encoding='utf-8') as file:
        #    file.write(dump)
        doc2 = cabocha_extended.load_from_text(dump)[0]
        #dump2 = cabocha_extended.dump(doc2)
        #with open('dat/log/cabocha_test.txt', 'w', encoding='utf-8') as file:
        #    file.write(dump2)
        
        for tok, tok2 in zip(nlelement.tokens(doc), nlelement.tokens(doc2)):
            self.assertEqual(tok.surface, tok2.surface)
            if hasattr(tok, "predicate_term"):
                for item1, item2 in zip(tok.predicate_term.items(), tok2.predicate_term.items()):
                    self.assertEqual(item1[0], item2[0])
                    self.assertEqual(len(item1[1]), len(item2[1]))
                    for val1, val2 in zip(item1[1], item2[1]):
                        self.assertEqual(val1.ana_ref(), val2.ana_ref())
                        self.assertEqual(val1.ant_ref(), val2.ant_ref())
                        self.assertAlmostEqual(val1.label, val2.label)
                        self.assertAlmostEqual(val1.probable, val2.probable)
                        self.assertEqual(val1.case, item1[0])
                        self.assertEqual(val2.case, item2[0])    
            elif hasattr(tok2, "predicate_term"):
                self.fail("predicate argument located invalid position")                    
            if hasattr(tok, "coreference"):
                for val1, val2 in zip(tok.coreference, tok2.coreference):
                    self.assertEqual(val1.ana_ref(), val2.ana_ref())
                    self.assertEqual(val1.ant_ref(), val2.ant_ref())
                    self.assertAlmostEqual(val1.label, val2.label)
                    self.assertAlmostEqual(val1.probable, val2.probable)
            elif hasattr(tok2, "coreference"):
                self.fail("coreference argument located invalid position")


    def tearDown(self):
        self.samples = None
