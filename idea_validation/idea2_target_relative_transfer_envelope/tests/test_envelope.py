import copy
import hashlib
import inspect
import json
import unittest
from collections import Counter
from fractions import Fraction
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import schema
import policy_geometry as geometry
from build_cases import CASES,source_records,target_records,encode,BASE_SOURCE,P4_IN,P4_OUT
from baselines import m1,digest
from launcher import launch,success,denial_probe,CANDIDATE_FILES,LEGACY
from evaluate import exact_membership,independent_counts,paired_checks,compute_gates,verdict
from integrity import history_matches,make_lock,check_lock
from render_report import scope_ok
from run_experiment import scientific

class EnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[]
        for i,(pair,side,sp,tp) in enumerate(CASES):
            source=source_records(sp);target=target_records(tp)
            sb,tb=encode(source),encode(target)
            run=launch(sb,tb);out=success(run)
            official=scientific(success(launch(sb,official=True)))
            valid_s,vs=independent_counts(source,True)
            valid_t,vt=independent_counts(target,False)
            cls.rows.append(dict(pair=pair,side=side,probe=scientific(out),
                source_sha256=hashlib.sha256(sb).hexdigest(),run=run,
                data_integrity=valid_s and valid_t,
                descriptors_match=vs==out["source_policy_vectors"] and vt["target"]==out["target_policy_vector"],
                global_equivalence=official==out["global"],
                independent_geometry=exact_membership(list(vs.values()),vt["target"])))
        cls.checks=paired_checks(cls.rows)
    def bad_target(self,field,value):
        row={"state":"S0","action":"A",field:value}
        with self.assertRaises(ValueError): schema.validate(row,False)
    def test_exact_source_outcomes(self):
        for _,_,sp,_ in CASES:
            valid,_=independent_counts(source_records(sp),True)
            self.assertTrue(valid)
    def test_source_schema(self):
        schema.validate({"era_id":"e000","state":"S0","action":"A","outcome":1},True)
        with self.assertRaises(ValueError): schema.validate({"state":"S0","action":"A","outcome":1},True)
    def test_target_schema(self):
        schema.validate({"state":"S1","action":"B"},False)
        with self.assertRaises(ValueError): schema.validate({"state":"S1"},False)
    def test_target_outcome_rejected(self): self.bad_target("outcome",1)
    def test_gamma_rejected(self): self.bad_target("gamma",.5)
    def test_policy_name_rejected(self): self.bad_target("policy_name","foo")
    def test_expected_status_rejected(self): self.bad_target("expected_status","TRANSFERABLE")
    def test_world_and_vectors_rejected(self):
        for field in ["world","case_label","inside","outside","true_utility","expected_decision","source_vector","target_vector"]:
            self.bad_target(field,"hidden")
    def test_source_extras_rejected(self):
        for key in ["gamma","policy_name","world","target_vector"]:
            with self.assertRaises(ValueError):
                schema.validate({"era_id":"e000","state":"S0","action":"A","outcome":1,key:0},True)
    def test_bool_outcome_rejected(self):
        with self.assertRaises(ValueError):
            schema.validate({"era_id":"e000","state":"S0","action":"A","outcome":True},True)
    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"state":"S0","state":"S1","action":"A"}',object_pairs_hook=schema.unique_object)
    def test_semantic_era_rejected(self):
        with self.assertRaises(ValueError):
            schema.validate({"era_id":"P1_inside","state":"S0","action":"A","outcome":1},True)
    def test_exact_state_counts(self):
        for _,_,sp,tp in CASES:
            schema.validate_counts(source_records(sp),True)
            schema.validate_counts(target_records(tp),False)
        with self.assertRaises(ValueError): schema.validate_counts(target_records((50,50))[:-1],False)
    def test_descriptor_reconstruction(self):
        self.assertEqual(geometry.descriptor(target_records((20,80))),(Fraction(1,5),Fraction(4,5)))
        self.assertTrue(all(r["descriptors_match"] for r in self.rows))
    def test_tv_distance(self):
        self.assertEqual(geometry.tv((Fraction(1,5),Fraction(1,5)),(Fraction(4,5),Fraction(1,5))),Fraction(3,10))
    def test_global_cert_equivalence_primary(self):
        self.assertTrue(all(r["global_equivalence"] for r in self.rows))
    def test_global_cert_equivalence_legacy_fixed_inputs(self):
        for p in sorted((LEGACY/"export").glob("case_*.jsonl")):
            current=scientific(success(launch(p.read_bytes(),official=True)))
            previous=scientific(json.loads((LEGACY/"results/candidate_outputs"/(p.stem+".json")).read_text()))
            self.assertEqual(current,previous,p.name)
    def test_convex_inside(self):
        self.assertTrue(geometry.membership([(0,0),(1,0),(0,1)],(Fraction(1,4),Fraction(1,4)))["inside"])
    def test_convex_outside(self):
        self.assertFalse(geometry.membership([(0,0),(1,0),(0,1)],(1,1))["inside"])
    def test_linprog_residual(self):
        for r in self.rows:
            o=r["probe"]
            if o["target_in_convex_hull"]: self.assertLessEqual(o["linprog_residual"],1e-10)
    def test_convex_weights_reconstruct(self):
        for r in self.rows:
            o=r["probe"];w=o["convex_weights"]
            if w is None: continue
            self.assertAlmostEqual(sum(w.values()),1,places=10)
            self.assertTrue(all(v>=-1e-10 for v in w.values()))
            for i in range(2):
                self.assertAlmostEqual(sum(weight*float(Fraction(o["source_policy_vectors"][e][i])) for e,weight in w.items()),
                                       float(Fraction(o["target_policy_vector"][i])),places=10)
    def test_p1_source_sha_equality(self): self.assertTrue(self.checks["P1"]["source_sha_equal"])
    def test_p1_m1_equality(self): self.assertTrue(self.checks["P1"]["utility_equal"])
    def test_p1_global_equality(self): self.assertTrue(self.checks["P1"]["global_equal"])
    def test_p1_transfer_inequality(self): self.assertTrue(self.checks["P1"]["transfer_pair"])
    def test_p2_provenance_sha_equality(self): self.assertTrue(self.checks["P2"]["provenance_sha_equal"])
    def test_p3_full_summary_sha_equality(self): self.assertTrue(self.checks["P3"]["source_summary_sha_equal"])
    def test_p3_summary_completeness(self):
        required={"M1","total_observations","per_era_observation_counts","mean_era_gap","variance_era_gap",
          "min_era_gap","max_era_gap","C_pos","C_neg","C_conflict","D_policy","number_of_eras",
          "effective_distinct_pairs","GlobalCertification"}
        self.assertEqual(set(self.rows[4]["probe"]["source_summary"]),required)
        self.assertTrue(self.checks["P3"]["source_summary_canonical_equal"])
    def test_p4_min_distance_equality(self):
        self.assertTrue(self.checks["P4"]["min_distance_equal"])
        for r in self.rows[6:]: self.assertEqual(r["probe"]["target_min_TV_exact"],"1/10")
    def test_p4_hull_inequality(self): self.assertTrue(self.checks["P4"]["hull_pair"])
    def test_p4_both_global_certified(self): self.assertTrue(self.checks["P4"]["global_both_prescriptive"])
    def test_m1_exact(self):
        for r in self.rows:
            self.assertEqual(r["probe"]["source_summary"]["M1"],{"U_A":"4/5","U_B":"2/5","gap":"2/5"})
    def test_candidate_cannot_see_private_labels(self):
        forbidden=["build_cases","evaluate","case_manifest","P1","P2","P3","P4","expected_status"]
        for name in CANDIDATE_FILES:
            text=(BASE/name).read_text()
            self.assertFalse(any(token in text for token in forbidden),name)
        for r in self.rows:
            files=r["run"]["output"]["execution_audit"]["initial_files"]
            self.assertFalse(any("private" in f or "manifest" in f or "P1" in f for f in files))
            self.assertTrue(r["run"]["filesystem_isolation_pass"])
            self.assertTrue(r["run"]["environment_isolation_pass"])
    def test_private_read_denied(self): self.assertTrue(denial_probe())
    def test_cli_extra_rejected(self):
        source=encode(source_records(BASE_SOURCE))
        target=target_records((50,40));target[0]["outcome"]=1
        self.assertNotEqual(launch(source,encode(target))["returncode"],0)
    def test_deterministic_rerun(self):
        a=launch(encode(source_records(BASE_SOURCE)),encode(target_records((50,40))))
        b=launch(encode(source_records(BASE_SOURCE)),encode(target_records((50,40))))
        self.assertEqual(a["output_sha256"],b["output_sha256"])
    def test_gate_boundary_decision(self):
        self.assertEqual(geometry.decision("PROVISIONAL",True),"GLOBAL_NOT_CERTIFIED")
        self.assertEqual(geometry.decision("PRESCRIPTIVE",True),"TRANSFERABLE")
        self.assertEqual(geometry.decision("PRESCRIPTIVE",False),"OUT_OF_ENVELOPE")
    def test_gate_verdict_boundaries(self):
        allpass={f"G{i}":True for i in range(10)}
        self.assertEqual(verdict(allpass),"TARGET_RELATIVE_ENVELOPE_GO")
        self.assertEqual(verdict(allpass,requires_target_outcome=True),"TARGET_RELATIVE_ENVELOPE_NO_GO")
        self.assertEqual(verdict({**allpass,"G5":False}),"TARGET_RELATIVE_ENVELOPE_NARROW")
        self.assertEqual(verdict({k:False for k in allpass}),"TARGET_RELATIVE_ENVELOPE_NO_GO")
    def test_history_unchanged_logic(self):
        self.assertTrue(history_matches())
        baseline=json.loads((BASE/"results/history_before.json").read_text())
        changed=copy.deepcopy(baseline);first=next(iter(changed));changed[first]["sha256"]="bad"
        self.assertNotEqual(changed,baseline)
    def test_no_threshold_tuning_path(self):
        self.assertEqual(geometry.METHOD,"highs")
        self.assertEqual(geometry.RESIDUAL_TOLERANCE,1e-10)
        self.assertEqual(list(inspect.signature(geometry.membership).parameters),["points","target"])
        self.assertEqual(list(inspect.signature(geometry.decision).parameters),["global_status","inside"])
        config=json.loads((BASE/"public_config.json").read_text())
        self.assertEqual(config["residual_tolerance"],geometry.RESIDUAL_TOLERANCE)
        self.assertEqual(config["global_config_sha256"],hashlib.sha256((LEGACY/"public_config.json").read_bytes()).hexdigest())
    def test_independent_geometry_all(self):
        for r in self.rows:
            self.assertEqual(r["independent_geometry"]["inside"],r["probe"]["target_in_convex_hull"])
    def test_boundary_vertex_segment(self):
        points=[(Fraction(0),Fraction(0)),(Fraction(1),Fraction(0))]
        for target in [(0,0),(Fraction(1,2),0)]:
            self.assertTrue(geometry.membership(points,target)["inside"])
            self.assertTrue(exact_membership(points,target)["inside"])
        self.assertFalse(exact_membership(points,(Fraction(1,2),Fraction(1,10)))["inside"])
    def test_frozen_inputs_hash_lock_logic(self):
        lock=make_lock();self.assertTrue(check_lock(lock))
        lock["files"]["policy_geometry.py"]="bad";self.assertFalse(check_lock(lock))
    def test_scope_discipline(self): self.assertTrue(scope_ok())
    def test_all_gates_on_prefomal_fixtures(self):
        gates=compute_gates(self.rows,self.checks,True,scope_ok(),True)
        self.assertTrue(all(gates.values()),gates)

if __name__=="__main__": unittest.main(verbosity=2)
