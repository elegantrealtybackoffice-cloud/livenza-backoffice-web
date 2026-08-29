#!/usr/bin/env python3
"""Explicit, idempotent migration from the legacy Room/Tenant tables.

Names are copied for display only and are never used as an automatic identity match.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from livenza_legacy_core import resolve_customer_action, room_source_key
from livenza_customer_core import normalize_mobile


def _email(value):
    raw=str(value or '').strip().lower()
    return raw if raw and '@' in raw else ''


def _mobile(value):
    try: return normalize_mobile(value)
    except Exception: return ''


def build_parser():
    parser=argparse.ArgumentParser(description='Migrate legacy Livenza back-office entities into the unified V1 model.')
    parser.add_argument('--source',default='legacy_backoffice',choices=['legacy_backoffice'])
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true',dest='dry_run')
    mode.add_argument('--apply',action='store_true')
    parser.add_argument('--strict',action='store_true',help='Exit non-zero when unresolved conflicts are found.')
    return parser


def run(args):
    from app import app, db, Tenant, Room, Customer, CustomerIdentity, StayProperty, StayInventoryUnit, LegacyEntityMap
    counts={'customer_create':0,'customer_link':0,'room_create':0,'room_link':0,'conflict':0,'skip':0}
    dry_run=bool(args.dry_run)
    with app.app_context():
        for tenant in Tenant.query.order_by(Tenant.id).all():
            source_id=str(tenant.id)
            mapping=LegacyEntityMap.query.filter_by(source_system=args.source,source_entity_type='tenant',source_id=source_id).first()
            mapped_customer_id=mapping.livenza_entity_id if mapping and mapping.livenza_entity_type=='customer' else None
            mobile=_mobile(tenant.tenant_mobile); email=_email(tenant.tenant_email)
            mobile_matches=[]; email_matches=[]
            if mobile:
                mobile_matches=[r.customer_id for r in CustomerIdentity.query.filter_by(provider='mobile',identifier=mobile).filter(CustomerIdentity.verified_at.isnot(None)).all()]
            if email:
                email_matches=[r.customer_id for r in CustomerIdentity.query.filter_by(provider='email',identifier=email).filter(CustomerIdentity.verified_at.isnot(None)).all()]
            action=resolve_customer_action(mapped_customer_id,mobile_matches,email_matches)
            if action['action']=='conflict':
                counts['conflict']+=1; continue
            if action['action']=='link':
                counts['customer_link']+=1; customer_id=action['customer_id']
            else:
                counts['customer_create']+=1
                if dry_run: continue
                customer=Customer(public_id=str(uuid.uuid4()),full_name=(tenant.tenant_name or '').strip(),primary_mobile=mobile,primary_email=email,status='active')
                db.session.add(customer); db.session.flush(); customer_id=customer.id
            if not mapping and not dry_run:
                db.session.add(LegacyEntityMap(source_system=args.source,source_entity_type='tenant',source_id=source_id,livenza_entity_type='customer',livenza_entity_id=customer_id,metadata_json=json.dumps({'legacy_status':tenant.status or ''})))

        for room in Room.query.order_by(Room.id).all():
            source_id=str(room.id)
            mapping=LegacyEntityMap.query.filter_by(source_system=args.source,source_entity_type='room',source_id=source_id).first()
            if mapping:
                counts['room_link']+=1; continue
            try: room_source_key(room.property_name,room.room_no)
            except ValueError:
                counts['skip']+=1; continue
            props=StayProperty.query.filter(db.func.lower(StayProperty.name)==str(room.property_name or '').strip().lower()).all()
            if len(props)!=1:
                counts['conflict']+=1; continue
            prop=props[0]
            existing=StayInventoryUnit.query.filter_by(property_id=prop.id,unit_type='room',code=str(room.room_no or '').strip()).first()
            if existing:
                counts['room_link']+=1; unit_id=existing.id
            else:
                counts['room_create']+=1
                if dry_run: continue
                unit=StayInventoryUnit(property_id=prop.id,parent_id=None,room_category_id=None,unit_type='room',code=str(room.room_no or '').strip(),display_name=f'Room {room.room_no}',allocatable=True,active=True)
                db.session.add(unit); db.session.flush(); unit_id=unit.id
            if not dry_run:
                meta={'capacity':room.capacity or '','standard_tariff':room.standard_tariff or '','legacy_room_type':room.room_type or ''}
                db.session.add(LegacyEntityMap(source_system=args.source,source_entity_type='room',source_id=source_id,livenza_entity_type='stay_inventory_unit',livenza_entity_id=unit_id,metadata_json=json.dumps(meta)))

        if dry_run:
            db.session.rollback()
        else:
            db.session.commit()
    print(json.dumps(counts,sort_keys=True))
    if args.strict and counts['conflict']:
        return 2
    return 0


def main(argv=None):
    args=build_parser().parse_args(argv)
    return run(args)


if __name__=='__main__':
    raise SystemExit(main())
