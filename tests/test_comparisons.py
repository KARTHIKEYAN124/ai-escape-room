import unittest
from scripts.compare_versions import CASES, run_case

class ComparisonTests(unittest.TestCase):
    def test_seven_faults_are_contained_by_version_two(self):
        for case in CASES:
            with self.subTest(case=case[0]):
                result = run_case(case)
                self.assertEqual(result['v1_response'], case[2])
                self.assertTrue(result['v2_integrity_pass'], result)
                self.assertFalse(result['v2_state']['escaped'])
                self.assertNotEqual(result['v1_response'], result['v2_response'])
