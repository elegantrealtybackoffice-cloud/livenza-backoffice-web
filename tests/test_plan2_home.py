from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'web/src/app/page.tsx'

def test_home_contains_approved_sections_in_order():
    text=PAGE.read_text()
    labels=['LIVE MORE.','One life. Many Livenza experiences.','Find your place.','Find your city',"Life isn't a room",'WEAR THE LIFE.','The Livenza Standard','Real residents. Real Livenza.','FROM WHERE YOU STAY']
    positions=[]
    for label in labels:
        idx=text.find(label)
        assert idx >= 0, f'missing {label}'
        positions.append(idx)
    assert positions == sorted(positions)


def test_home_links_operational_and_future_verticals():
    text=PAGE.read_text()
    for href in ['/stays','/store','/fit','/groom','/skin','/media']:
        assert f'href="{href}"' in text
