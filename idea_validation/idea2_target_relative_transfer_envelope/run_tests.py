import json
import sys
import unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent
class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.passed_names=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.passed_names.append(test._testMethodName)
def main():
    suite=unittest.defaultTestLoader.discover(str(BASE/"tests"),pattern="test_*.py")
    runner=unittest.TextTestRunner(verbosity=2,resultclass=Result)
    result=runner.run(suite)
    record={"tests_run":result.testsRun,"tests_passed":len(result.passed_names),
            "passed_names":sorted(result.passed_names),"success":result.wasSuccessful(),
            "failures":[str(t) for t,_ in result.failures],"errors":[str(t) for t,_ in result.errors],
            "skipped":[str(t) for t,_ in result.skipped]}
    (BASE/"results/preformal_tests.json").write_text(json.dumps(record,indent=2)+"\n")
    if not result.wasSuccessful(): sys.exit(1)
if __name__=="__main__": main()
