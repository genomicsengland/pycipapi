

Create a client as follows.
```
from pycipapi.cipapi_client import CipApiClient
cipapi = CipApiClient("https://cipapi.fake", user="*****", password="*****")
```

The client gets a token from the CIPAPI and renews it if expired.
Every failed request due to a connectivity issue is retried following an exponential back off retry policy.

## Pull data from the CIPAPI
Fetch a specific case as follows. Both cases for rare disease and cancer are supported.

```
# id = 1234; version = 1
case = cipapi.get_case("1234", "1")
```

Alternatively iterate through all interpretation requests as follows.

```
for case in cipapi.get_cases():
    # do whatever with the case
```

## Get the latest entities from a case

Fetch the latest case entities. If there are multiple interpreted genomes for a given interpretation request it will return the latest.
All entities are migrated to the latest version of the models (ie: reports 5.0.0 and participants 1.1.0)

```
ir = case.get_interpretation_request()
if case.is_cancer():
    self.assertTrue(CancerInterpretationRequest.validate(ir.toJsonDict()))
elif case.is_rare_disease():
    self.assertTrue(InterpretationRequestRD.validate(ir.toJsonDict()))
    
tig = case.get_tiering_interpreted_genome()
for variant in tig.variants:
    # do something with your variant...

cr = case.get_clinical_report()
ig = case.get_interpreted_genome()
ped = case.get_pedigree()
eq = case.get_exit_questionnaire()
```
