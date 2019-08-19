pycipapi is a python client to the Interpretation API (CIP-API) REST API. 
pycipapi primary aim is to facilitate access to the REST API, allowing the users to manage and take actions on cases 
in a easy way. 

## Initialise the client

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
