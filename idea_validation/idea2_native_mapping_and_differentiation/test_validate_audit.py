"""Negative fixtures test validation rather than restating research judgments."""
import copy
import unittest
import validate_audit as v

class AuditTests(unittest.TestCase):
    def test_schema_missing_column(self):
        with self.assertRaises(ValueError):
            v.schema([{"a":"1"}], {"a","b"})
    def test_duplicate_paper(self):
        r=v.csv_read("literature/paper_matrix.csv")[0]
        with self.assertRaises(ValueError):
            v.check_papers([r,copy.deepcopy(r)])
    def test_missing_source(self):
        r=copy.deepcopy(v.csv_read("literature/paper_matrix.csv")[0])
        r["verified_source"]=""
        with self.assertRaises(ValueError):
            v.check_papers([r])
    def test_missing_native_evidence(self):
        r=copy.deepcopy(v.csv_read("native_mapping/native_field_matrix.csv")[0])
        r["state_source"]="theoretically available"
        with self.assertRaises(ValueError):
            v.check_native([r])
    def test_native_enum(self):
        r=copy.deepcopy(v.csv_read("native_mapping/native_field_matrix.csv")[0])
        r["policy_id_native"]="MAYBE"
        with self.assertRaises(ValueError):
            v.check_native([r])
    def test_mapping_enum(self):
        r=copy.deepcopy(v.csv_read("native_mapping/policy_era_feasibility.csv")[0])
        r["mapping_level"]="M1"
        with self.assertRaises(ValueError):
            v.check_eras([r])
    def test_claim_enum(self):
        papers=v.csv_read("literature/paper_matrix.csv")
        rows=v.csv_read("literature/claim_collision_matrix.csv")
        rows[0]["C1"]="SIMILAR"
        with self.assertRaises(ValueError):
            v.check_claims(rows,papers)
    def test_claim_missing_paper(self):
        with self.assertRaises(ValueError):
            v.check_claims(v.csv_read("literature/claim_collision_matrix.csv")[:-1],
                           v.csv_read("literature/paper_matrix.csv"))
    def test_native_boundary_cases(self):
        self.assertEqual(v.native_verdict({"JitRL":"MAP-L2","MemRL":"MAP-L3"}),"NATIVE_MAPPING_NO_GO")
        self.assertEqual(v.native_verdict({"JitRL":"MAP-L1"}),"NATIVE_MAPPING_NARROW")
        self.assertEqual(v.native_verdict({"ExpeL":"MAP-L0","Reflexion":"MAP-L0"}),"NATIVE_MAPPING_NARROW")
        self.assertEqual(v.native_verdict({"JitRL":"MAP-L1","Reflexion":"MAP-L0"}),"NATIVE_MAPPING_GO")
    def test_diff_kill_precedence(self):
        self.assertEqual(v.differentiation_verdict(True,True,False),"DIFFERENTIATION_NO_GO")
        self.assertEqual(v.differentiation_verdict(False,True,True),"DIFFERENTIATION_BORDERLINE")
        self.assertEqual(v.differentiation_verdict(False,True,False),"DIFFERENTIATION_GO")
    def test_all_combined_boundaries(self):
        for n in ["GO","NARROW","NO_GO"]:
            for d in ["GO","BORDERLINE","NO_GO"]:
                expected="STAGE6B_NO_GO" if "NO_GO" in (n,d) else (
                    "STAGE6B_GO" if n==d=="GO" else "STAGE6B_NARROW")
                self.assertEqual(v.combined_verdict("NATIVE_MAPPING_"+n,"DIFFERENTIATION_"+d),expected)
    def test_positive_real_matrices(self):
        v.check_native(v.csv_read("native_mapping/native_field_matrix.csv"))
        v.check_eras(v.csv_read("native_mapping/policy_era_feasibility.csv"))
        v.check_papers(v.csv_read("literature/paper_matrix.csv"))
        v.check_claims(v.csv_read("literature/claim_collision_matrix.csv"),
                       v.csv_read("literature/paper_matrix.csv"))

if __name__=="__main__":
    unittest.main(verbosity=2)
