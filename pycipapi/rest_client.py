import abc
import datetime
import logging
import requests

try:
    import urlparse
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except:
    from urllib import parse as urlparse
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

from requests.compat import urljoin
from requests.exceptions import HTTPError


class NotFound(HTTPError):

    pass


class BlockedCase(HTTPError):

    pass


def requests_retry_session(retries=5, backoff_factor=0.8, status_forcelist=(500, 502, 504, 503), session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def func_wrapper_multi(func, klass, *args, **kwargs):
    for item in func(*args, **kwargs):
        yield klass(**item)


def func_wrapper_single(func, klass, *args, **kwargs):
    return klass(**func(*args, **kwargs))


def returns_item(klass, multi=False):
    def item_decorator(func):
        def func_wrapper(*args, **kwargs):
            if multi:
                return func_wrapper_multi(func, klass, *args, **kwargs)
            else:
                return func_wrapper_single(func, klass, *args, **kwargs)
        return func_wrapper
    return item_decorator


class RestClient(object):
    session = requests.Session()
    _request_methods = {
        'post': requests_retry_session(session=session).post,
        'get': requests_retry_session(session=session).get,
        'delete': requests_retry_session(session=session).delete,
        'put': requests_retry_session(session=session).put,
        'patch': requests_retry_session(session=session).patch,
    }

    def __init__(self, url_base, retries=None, fixed_params=None):
        self.fixed_params = fixed_params if fixed_params is not None else {}
        self.url_base = url_base
        self.headers = {
            'Accept': 'application/json'
        }
        self.token = None
        self.renewed_token = False
        if retries is not None:
            self._request_methods = {
                'post': requests_retry_session(session=self.session, retries=retries).post,
                'get': requests_retry_session(session=self.session, retries=retries).get,
                'delete': requests_retry_session(session=self.session, retries=retries).delete,
                'put': requests_retry_session(session=self.session, retries=retries).put,
                'patch': requests_retry_session(session=self.session, retries=retries).patch,
            }

    @staticmethod
    def build_url(baseurl, path, *args):
        url = urljoin(baseurl, path)
        if args:
            url_args = '/'.join(map(str, args))
            url.rstrip('/')
            url = url + '/' + url_args
        return url

    def set_authenticated_header(self, renew_token=False):
        if not self.token or renew_token:
            self.token = self.get_token()
        self.headers["Authorization"] = "{token}".format(token=self.token)

    @abc.abstractmethod
    def get_token(self):
        raise ValueError("Not implemented")

    @abc.abstractmethod
    def get_paginated(self, url, **kwargs):
        raise ValueError("Not implemented")

    @staticmethod
    def _clean_url(parameters, url):
        query_params = urlparse.parse_qs(urlparse.urlparse(url).query)
        url_as_list = list(urlparse.urlsplit(url))
        # removing query params
        url_as_list[3] = ''
        url = urlparse.urlunsplit(url_as_list)
        parameters.update(query_params)
        return parameters, url

    def _request_call(self, method, url, params, payload=None, files=None):
        parameters = self.fixed_params if self.fixed_params is not None else {}
        if params is not None:
            parameters.update(params)

        if url is None:
            raise ValueError("Must define endpoint before {method}".format(method=method))
        logging.debug("{date} {method} {url}".format(
            date=datetime.datetime.now(),
            method=method.upper(),
            url="{}?{}".format(url, "&".join(["{}={}".format(k, v) for k, v in parameters.items()]))
        ))
        request_method = self._request_methods.get(method)
        if request_method is None:
            raise NotImplementedError
        if payload and files:
            return request_method(url, json=payload, files=files, params=parameters, headers=self.headers)
        elif files:
            return request_method(url, json=payload, params=parameters, headers=self.headers)
        elif payload:
            return request_method(url, json=payload, params=parameters, headers=self.headers)
        return request_method(url, params=parameters, headers=self.headers)

    def post(self, url, payload, files=None, params=None):
        response = self._request_call('post', url, params=params, files=files, payload=payload)
        response = self._verify_response(response, 'post', url=url, params=params, files=files, payload=payload)
        return response.json() if response.content else None

    def put(self, url, payload, params=None):
        response = self._request_call('put', url, params=params, payload=payload)
        response = self._verify_response(response, 'put', url=url, params=params, payload=payload)
        return response.json() if response.content else None

    def patch(self, url, payload, params=None):
        response = self._request_call('patch', url, params=params, payload=payload)
        response = self._verify_response(response, 'patch', url=url, params=params, payload=payload)
        return response.json() if response.content else None

    def get(self, url, params=None):
        response = self._request_call('get', url, params=params)
        response = self._verify_response(response, 'get', url=url, params=params)
        return response.json() if response.content else None

    def delete(self, url, params=None):
        response = self._request_call('delete', url, params=params)
        response = self._verify_response(response, 'delete', url=url, params=params)
        return response.json() if response.content else None

    def _verify_response(self, response, method=None, **kwargs):
        logging.debug("{date} response status code {status}".format(
            date=datetime.datetime.now(),
            status=response.status_code)
        )
        if response.status_code not in (200, 203, 206, 201):
            logging.error(response.content)
            # first 403 renews the token, second 403 in a row fails
            if response.status_code == 403 and not self.renewed_token:
                # renews the token if unauthorised
                self.set_authenticated_header(renew_token=True)
                self.renewed_token = True
                return self._request_call(method, **kwargs)
            raise HTTPError("{}:{}".format(response.status_code, response.text), response=response)
        else:
            # once a 20X response token is not anymore just renewed, it can be renewed again if a 403 arrives
            self.renewed_token = False
            return response
