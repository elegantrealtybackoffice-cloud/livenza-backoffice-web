#!/usr/bin/env python3
"""Post-deploy verification for Livenza.life V1 without exposing PII."""
from __future__ import annotations
import argparse, json, os, sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def fetch(url, headers=None, expect_json=False, timeout=8):
    req=Request(url,headers={'User-Agent':'LivenzaPostDeploy/1.0',**(headers or {})})
    with urlopen(req,timeout=timeout) as response:
        data=response.read()
        if not (200 <= response.status < 300): raise RuntimeError(f'{response.status}')
        return json.loads(data.decode('utf-8') or '{}') if expect_json else data


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',required=True); parser.add_argument('--api-url',required=True)
    parser.add_argument('--booking-id'); parser.add_argument('--order-id')
    args=parser.parse_args(argv)
    base=args.base_url.rstrip('/'); api=args.api_url.rstrip('/')
    failures=[]
    for url,is_json in [(base+'/',False),(base+'/stays',False),(base+'/store',False),(api+'/api/v1/health',True)]:
        try: fetch(url,expect_json=is_json); print('PASS',url)
        except Exception as exc: failures.append(f'{url}: {exc}'); print('FAIL',url,exc)

    customer_session=(os.getenv('LIVENZA_CUSTOMER_SESSION_TOKEN') or '').strip()
    if customer_session:
        try:
            fetch(api+'/api/v1/me',headers={'Cookie':f'livenza_customer_session={customer_session}'},expect_json=True)
            print('PASS authenticated My Livenza')
        except Exception as exc:
            failures.append(f'My Livenza: {exc}')

    verify_token=(os.getenv('LIVENZA_POSTDEPLOY_TOKEN') or '').strip()
    if args.booking_id or args.order_id:
        if len(verify_token)<32:
            failures.append('LIVENZA_POSTDEPLOY_TOKEN is required for booking/order reconciliation checks.')
        else:
            headers={'Authorization':f'Bearer {verify_token}'}
            for kind,public_id in [('booking',args.booking_id),('order',args.order_id)]:
                if not public_id: continue
                url=f'{api}/admin/livenza/postdeploy/verify/{kind}/{public_id}'
                try:
                    result=fetch(url,headers=headers,expect_json=True)
                    if result.get('public_id') != public_id: raise RuntimeError('public id mismatch')
                    print('PASS',kind,public_id,result.get('status'),result.get('payment_status'))
                except Exception as exc:
                    failures.append(f'{kind} {public_id}: {exc}')
    if failures:
        print('\n'.join(failures),file=sys.stderr); return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
