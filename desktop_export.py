"""Export the existing Windows Back Office SQLite data to JSON for web migration."""
import os, sqlite3, json, datetime
DB=os.path.join(os.path.expanduser('~'),'AgreementStudioData','agreements.db')
OUT='livenza_desktop_export.json'
if not os.path.exists(DB):
    raise SystemExit(f'Database not found: {DB}')
con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
payload={'exported_at':datetime.datetime.now().isoformat(),'source':DB}
for table in ('agreements','rooms','tenant_records'):
    try: payload[table]=[dict(r) for r in con.execute(f'SELECT * FROM {table}').fetchall()]
    except Exception: payload[table]=[]
con.close()
with open(OUT,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
print(f'Created {OUT}')
