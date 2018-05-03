

Create a client as follows.
```
from pycipapi.cipapi_client import CipApiClient
cipapi = CipApiClient("https://cipapi.fake", user="*****", password="*****")
```

The client gets a token from the CIPAPI and renews it if expired.
Every failed request due to a connectivity issue is retried following an exponential back off retry policy.

Fetch a specific case as follows.

```
# id = 1234; version = 1
ir = cipapi.get_interpretation_request("1234", "1")
```

Fetch the latest interpreted genome or clinical report, or fetch the pedigree for an interpretation request as follows.

```
cr = cipapi.get_clinical_report(ir)
ig = cipapi.get_interpreted_genome(ir)
ped = cipapi.get_pedigree(ir)
```

Alternatively iterate through all interpretation requests as follows.

```
for ir in cipapi.get_interpretation_requests():
    # do whatever with the ir
```
