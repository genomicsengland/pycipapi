

Create a client as follows.
```
from pycipapi.cipapi_client import CipApiClient
cipapi = CipApiClient("https://cipapi.fake", user="*****", password="*****")
```

The client gets a token from the CIPAPI and renews it if expired.
Every failed request due to a connectivity issue is retried following an exponential back off retry policy.

Fetch a specific case as follows. Both cases for rare disease and cancer are supported.

```
# id = 1234; version = 1
case = cipapi.get_case("1234", "1")
```

Fetch the case entities in the latest version of the models (ie: reports 5.0.0 and participants 1.1.0)

```
ir = case.get_interpretation_request()
if case.program == Program.cancer:
    self.assertTrue(CancerInterpretationRequest.validate(ir.toJsonDict()))
elif case.program == Program.rare_disease:
    self.assertTrue(InterpretationRequestRD.validate(ir.toJsonDict()))
    
tig = case.get_tiering_interpreted_genome()
cr = case.get_clinical_report()
ig = case.get_interpreted_genome()
ped = case.get_pedigree()
eq = case.get_exit_questionnaire()
```

Alternatively iterate through all interpretation requests as follows.

```
for case in cipapi.get_cases():
    # do whatever with the case
```
