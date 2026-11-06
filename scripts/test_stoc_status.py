# Copyright (c) 2026 Christian Reitwiessner. Apache-2.0. Authors: Christian Reitwiessner.
import copy
import json
import unittest
from pathlib import Path
from stoc_status import check_state, extract_results, resources_for, validate

ROOT=Path(__file__).resolve().parent.parent
class StatusTests(unittest.TestCase):
    def test_no_checks_does_not_pass(self):
        self.assertEqual(check_state([],[]),'not reported')
        self.assertEqual(check_state([{'status':'in_progress','conclusion':None}],[]),'pending')
        self.assertEqual(check_state([{'status':'completed','conclusion':'failure'}],[]),'failed')
        self.assertEqual(check_state([{'status':'completed','conclusion':'success'}],[]),'reported checks passed')
    def test_unknown_tokens_are_not_zero(self):
        data={'measurements':[{'paper_id':1,'started_at':'2026-11-06T00:00:00Z','finished_at':'2026-11-06T00:01:00Z','total_tokens':None}]}
        resource=resources_for(1,data)
        self.assertEqual(resource['recorded_seconds'],60)
        self.assertIsNone(resource['tokens'])
        self.assertIsNone(resources_for(2,data)['recorded_seconds'])
    def test_exact_theorem_line_skips_comments_private_and_examples(self):
        source='/-- theorem fake : False -/\nnamespace A\nprivate theorem helper : True := by trivial\npublic theorem actual\n    (n : Nat) : n = n := by rfl\n-- lemma other : False\nexample : True := by trivial\nend A\n'
        results=extract_results(source,'Complexity/Test.lean','a'*40)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0]['name'],'actual')
        self.assertEqual(results[0]['line'],4)
        self.assertTrue(results[0]['url'].endswith('#L4'))
        self.assertNotIn('by rfl',results[0]['statement'])
    def test_registry_and_catalogue_consistent(self):
        catalogue=json.loads((ROOT/'stoc/catalogue.json').read_text())
        registry=json.loads((ROOT/'stoc/status.json').read_text())
        validate(catalogue,registry)
        self.assertEqual(len(catalogue['papers']),1665)
        bad=copy.deepcopy(registry);bad['papers'].append(bad['papers'][0])
        with self.assertRaises(ValueError): validate(catalogue,bad)
    def test_invalid_evidence_fails(self):
        catalogue=json.loads((ROOT/'stoc/catalogue.json').read_text())
        registry=json.loads((ROOT/'stoc/status.json').read_text())
        registry['papers'][0]['reviewed_sha']='main'
        with self.assertRaises(ValueError):validate(catalogue,registry)
if __name__=='__main__':unittest.main()
