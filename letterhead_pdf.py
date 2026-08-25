import hashlib
import html
import io
import json
from pathlib import Path

from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image as RLImage, KeepTogether,
)

ALIGNMENTS={'left':TA_LEFT,'center':TA_CENTER,'right':TA_RIGHT,'justify':TA_JUSTIFY}
SAFE_FONTS={'Helvetica','Helvetica-Bold','Helvetica-Oblique','Times-Roman','Times-Bold','Courier'}

def sha256_bytes(data):
    return hashlib.sha256(bytes(data or b'')).hexdigest()

def _template(render_input):
    raw=render_input.get('template') or {}
    margins=raw.get('margins_mm') or [18,18,18,18]
    if isinstance(margins,dict):
        top=float(margins.get('top',38)); right=float(margins.get('right',18)); bottom=float(margins.get('bottom',24)); left=float(margins.get('left',18))
    else:
        vals=list(margins)+[18,18,18,18]; top,right,bottom,left=[float(x or 18) for x in vals[:4]]
    header=raw.get('header') if isinstance(raw.get('header'),dict) else {}
    footer=raw.get('footer') if isinstance(raw.get('footer'),dict) else {}
    typography=raw.get('typography') if isinstance(raw.get('typography'),dict) else {}
    return {
        'organization_name':raw.get('organization_name') or header.get('brand') or 'Livenza Life LLP',
        'address':header.get('address') or raw.get('address') or '',
        'footer_text':footer.get('text') or raw.get('footer_text') or 'Livenza Life LLP',
        'confidentiality':footer.get('confidentiality') or '',
        'page_numbers':bool(footer.get('page_numbers',True)),
        'margins':(top,right,bottom,left),
        'body_font':typography.get('body_font') if typography.get('body_font') in SAFE_FONTS else 'Helvetica',
        'body_size':float(typography.get('body_size') or 10.5),
        'line_spacing':float(typography.get('line_spacing') or 1.35),
        'logo':render_input.get('logo'),
        'background':render_input.get('background'),
        'watermark':render_input.get('watermark'),
    }

def _image_reader(item):
    if not item: return None
    raw=item.get('bytes') if isinstance(item,dict) else item
    if not raw: return None
    try: return ImageReader(io.BytesIO(raw))
    except Exception: return None

def _runs_markup(block):
    if isinstance(block.get('runs'),list):
        parts=[]
        for run in block['runs']:
            text=html.escape(str((run or {}).get('text') or '')).replace('\n','<br/>')
            if (run or {}).get('bold'): text=f'<b>{text}</b>'
            if (run or {}).get('italic'): text=f'<i>{text}</i>'
            if (run or {}).get('underline'): text=f'<u>{text}</u>'
            parts.append(text)
        return ''.join(parts)
    return html.escape(str(block.get('text') or '')).replace('\n','<br/>')

def _draw_page(canvas,doc,cfg,reference):
    width,height=A4
    bg=_image_reader(cfg.get('background'))
    if bg:
        try: canvas.drawImage(bg,0,0,width=width,height=height,mask='auto',preserveAspectRatio=False)
        except Exception: pass
    watermark=_image_reader(cfg.get('watermark'))
    if watermark:
        try:
            canvas.saveState(); canvas.setFillAlpha(.10); canvas.drawImage(watermark,width*.24,height*.32,width=width*.52,height=height*.36,mask='auto',preserveAspectRatio=True,anchor='c'); canvas.restoreState()
        except Exception: pass
    logo=_image_reader(cfg.get('logo'))
    if logo:
        try: canvas.drawImage(logo,doc.leftMargin,height-31*mm,width=40*mm,height=17*mm,mask='auto',preserveAspectRatio=True,anchor='sw')
        except Exception: pass
    canvas.saveState(); canvas.setFillColor(colors.HexColor('#103267')); canvas.setFont('Helvetica-Bold',12); canvas.drawString(doc.leftMargin,height-16*mm,cfg['organization_name'][:80])
    if cfg.get('address'):
        canvas.setFont('Helvetica',7.5); canvas.setFillColor(colors.HexColor('#5d6779')); canvas.drawString(doc.leftMargin,height-21*mm,cfg['address'][:125])
    canvas.setStrokeColor(colors.HexColor('#103267')); canvas.setLineWidth(.8); canvas.line(doc.leftMargin,height-26*mm,width-doc.rightMargin,height-26*mm)
    canvas.setStrokeColor(colors.HexColor('#c8ced8')); canvas.setLineWidth(.5); canvas.line(doc.leftMargin,17*mm,width-doc.rightMargin,17*mm)
    canvas.setFillColor(colors.HexColor('#5d6779')); canvas.setFont('Helvetica',7); canvas.drawString(doc.leftMargin,11*mm,cfg['footer_text'][:120])
    if cfg.get('confidentiality'): canvas.drawCentredString(width/2,7.5*mm,cfg['confidentiality'][:100])
    if cfg.get('page_numbers'): canvas.drawRightString(width-doc.rightMargin,11*mm,f'Page {doc.page}')
    if reference: canvas.setFont('Helvetica-Bold',7.5); canvas.drawRightString(width-doc.rightMargin,height-16*mm,reference[:90])
    canvas.restoreState()

def render_letterhead_pdf(render_input):
    render_input=render_input or {}; document=render_input.get('document') or {}; cfg=_template(render_input); reference=str(render_input.get('reference_number') or '')
    top,right,bottom,left=cfg['margins']
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=left*mm,rightMargin=right*mm,topMargin=max(top,34)*mm,bottomMargin=max(bottom,22)*mm,title=str(document.get('title') or 'Livenza Document'),author='Livenza Life LLP')
    styles=getSampleStyleSheet(); body=ParagraphStyle('LivenzaBody',parent=styles['BodyText'],fontName=cfg['body_font'],fontSize=cfg['body_size'],leading=cfg['body_size']*cfg['line_spacing'],spaceAfter=5*mm,textColor=colors.HexColor('#172033'))
    heading=ParagraphStyle('LivenzaHeading',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=max(12,cfg['body_size']+2),leading=max(15,cfg['body_size']*1.35),spaceBefore=2*mm,spaceAfter=4*mm,textColor=colors.HexColor('#102c5e'))
    small=ParagraphStyle('LivenzaSmall',parent=body,fontSize=max(8,cfg['body_size']-1),leading=max(10,cfg['body_size']*1.15),spaceAfter=2.5*mm)
    story=[]
    if reference: story.append(Paragraph(f'<b>Reference:</b> {html.escape(reference)}',small))
    if document.get('date'): story.append(Paragraph(f'<b>Date:</b> {html.escape(str(document.get("date")))}',small))
    if document.get('addressee'): story.extend([Spacer(1,2*mm),Paragraph(html.escape(str(document.get('addressee'))),body)])
    if document.get('subject'): story.append(Paragraph(f'<b>Subject: {html.escape(str(document.get("subject")))}</b>',heading))
    for block in document.get('body_sections') or []:
        if not isinstance(block,dict): continue
        kind=block.get('type') or 'paragraph'
        if kind=='page_break': story.append(PageBreak()); continue
        if kind in ('paragraph','heading'):
            style=heading if kind=='heading' else ParagraphStyle('dynamic',parent=body,alignment=ALIGNMENTS.get(block.get('align','left'),TA_LEFT))
            story.append(Paragraph(_runs_markup(block) or '&nbsp;',style)); continue
        if kind in ('bullet_list','numbered_list'):
            for idx,item in enumerate(block.get('items') or [],1):
                text=item if isinstance(item,str) else (item or {}).get('text','')
                prefix='•' if kind=='bullet_list' else f'{idx}.'
                story.append(Paragraph(f'{prefix}&nbsp;&nbsp;{html.escape(str(text))}',body))
            continue
        if kind=='table':
            rows=[]
            for raw_row in block.get('rows') or []:
                row=[]
                for cell in raw_row if isinstance(raw_row,list) else []:
                    if isinstance(cell,dict): cell_text=''.join(str((r or {}).get('text') or '') for r in cell.get('runs',[])) or str(cell.get('text') or '')
                    else: cell_text=str(cell or '')
                    row.append(Paragraph(html.escape(cell_text),small))
                if row: rows.append(row)
            if rows:
                table=Table(rows,hAlign='LEFT',repeatRows=1); table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.35,colors.HexColor('#c7cfdb')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)])); story.extend([table,Spacer(1,4*mm)])
    signature=render_input.get('signature')
    if signature:
        flow=[]; raw=signature.get('bytes') if isinstance(signature,dict) else None
        if raw:
            try:
                img=RLImage(io.BytesIO(raw),width=38*mm,height=18*mm); img._restrictSize(42*mm,22*mm); flow.append(img)
            except Exception: pass
        if isinstance(signature,dict):
            if signature.get('name'): flow.append(Paragraph(f'<b>{html.escape(str(signature["name"]))}</b>',small))
            if signature.get('designation'): flow.append(Paragraph(html.escape(str(signature['designation'])),small))
        if flow: story.extend([Spacer(1,12*mm),KeepTogether(flow)])
    doc.build(story,onFirstPage=lambda c,d:_draw_page(c,d,cfg,reference),onLaterPages=lambda c,d:_draw_page(c,d,cfg,reference))
    return buf.getvalue()

def _image_to_pdf(raw):
    image=PILImage.open(io.BytesIO(raw)).convert('RGB'); width,height=A4; margin=12*mm
    iw,ih=image.size; scale=min((width-2*margin)/max(iw,1),(height-2*margin)/max(ih,1)); draw_w=iw*scale; draw_h=ih*scale
    from reportlab.pdfgen import canvas
    out=io.BytesIO(); c=canvas.Canvas(out,pagesize=A4); c.drawImage(ImageReader(image),(width-draw_w)/2,(height-draw_h)/2,width=draw_w,height=draw_h,preserveAspectRatio=True,mask='auto'); c.showPage(); c.save(); return out.getvalue()

def merge_annexures(base_pdf,annexures):
    writer=PdfWriter()
    for page in PdfReader(io.BytesIO(base_pdf)).pages: writer.add_page(page)
    for item in annexures or []:
        if not isinstance(item,(tuple,list)) or len(item)<2: raise ValueError('Invalid annexure.')
        label,mraw=item[0],item[1]; raw=bytes(mraw or b''); key=str(label or '').lower()
        if key in ('application/pdf','pdf') or raw.startswith(b'%PDF'):
            annex_pdf=raw
        elif key in ('image/jpeg','image/jpg','image/png','image/webp','jpeg','jpg','png','webp') or key.endswith(('.jpg','.jpeg','.png','.webp')):
            annex_pdf=_image_to_pdf(raw)
        else:
            raise ValueError('Unsupported annexure format. Only PDF, JPG, PNG and WebP can be issued in the final package.')
        for page in PdfReader(io.BytesIO(annex_pdf)).pages: writer.add_page(page)
    out=io.BytesIO(); writer.write(out); return out.getvalue()
