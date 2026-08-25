# Livenza Life Operations Cloud — Web 1.5.6

Web 1.5.6 repairs Aadhaar agreement autofill, keeps the Livenza mark completely inside the header, and introduces a stable low-cost mobile rendering path.

## Automatic Aadhaar agreement autofill

- Aadhaar JPG, PNG and PDF uploads now run through server-side OCR before any optional cloud AI enhancement.
- The automatic path no longer depends on OCR or AI configuration on the phone, tablet or Windows device.
- Text PDFs are parsed directly; image scans and photographed cards use bundled RapidOCR/ONNX models. Existing Tesseract installations remain a secondary local fallback.
- PDF pages are rendered in memory with bounded resolution. The uploaded identity document is not written to disk or logged.
- OpenAI vision remains an optional enhancement when `OPENAI_API_KEY` is available, but it is no longer required for normal automatic extraction.
- Extracted values are an autofill aid only. Staff must review the name, date of birth, address and identity number before saving; this does not verify Aadhaar authenticity with UIDAI.

Deploy the updated `requirements.txt` so `rapidocr`, `onnxruntime` and `PyMuPDF` are installed. No new environment key is required.

## Contained and compact header

- The L logo and its AI light effect are smaller, vertically centred and completely contained within the header.
- The logo no longer hangs over or obstructs the LIVE marquee.
- After scrolling, the header contracts and keeps only the applications button and a small L avatar visible.
- Account, Admin, Settings and Logout destinations are also available inside the applications menu so compact mode never hides required controls.

## Mobile stability

- Mobile, low-memory, low-CPU and data-saving devices are detected before the stylesheet loads to prevent the first-render shimmer.
- Expensive blur layers, moving atmosphere, particle wallpaper, tilt tracking, sheen animations and page-transition overlays are removed on those devices.
- Weather remains available with a small bounded particle count, then fades normally.
- Images use asynchronous decoding and lighter mobile variants. Hidden tabs pause animations automatically.
- Desktop keeps the full translucent design and animation system.

No database migration is required. After deployment, confirm `/version` returns `Web 1.5.6` and includes `server-local-ocr`, `contained-header-logo`, `compact-scroll-header` and `mobile-performance-mode`.
