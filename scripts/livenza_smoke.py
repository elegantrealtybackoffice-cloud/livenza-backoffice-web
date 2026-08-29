#!/usr/bin/env python3
"""Fast post-deploy smoke checks for public Livenza.life and API discovery."""
from __future__ import annotations
import argparse, json, sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def fetch(url, expect_json=False, timeout=5):
    request=Request(url,headers={'User-Agent':'LivenzaSmoke/1.0'})
    with urlopen(request,timeout=timeout) as response:
        body=response.read()
        if not (200 <= response.status < 300):
            raise RuntimeError(f'{url} returned {response.status}')
        if expect_json:
            return json.loads(body.decode('utf-8') or '{}')
        return body


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',required=True)
    parser.add_argument('--api-url',required=True)
    args=parser.parse_args(argv)
    base=args.base_url.rstrip('/'); api=args.api_url.rstrip('/')
    checks=[
        (base+'/',False),(base+'/stays',False),(base+'/store',False),
        (api+'/api/v1/cities',True),(api+'/api/v1/properties',True),(api+'/api/v1/health',True),
    ]
    failures=[]
    for url,is_json in checks:
        try:
            fetch(url,expect_json=is_json,timeout=5)
            print('PASS',url)
        except (HTTPError,URLError,ValueError,RuntimeError) as exc:
            failures.append(f'{url}: {exc}'); print('FAIL',url,exc)
    if failures:
        print('\n'.join(failures),file=sys.stderr); return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
