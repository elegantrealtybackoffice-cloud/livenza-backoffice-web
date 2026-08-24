# Livenza Back Office Web 1.3.1

This maintenance release adds:

- Livenza favicon + PWA/app icons for browser tabs, Edge/Chrome install and Windows pinning.
- Site web manifest and theme metadata.
- Footer layout fix: footer stays after page content and rests at the bottom of short pages.
- Agreement Studio Aadhaar document intake for JPG/JPEG/PNG/PDF.
- Aadhaar tenant autofill for name, father/spouse, DOB, permanent address, Aadhaar ID type/number.
- Aadhaar uploads are processed transiently and are not persisted by the application.
- OCR/autofill is not UIDAI authentication and must be reviewed before saving an agreement.

## Aadhaar extraction

Text PDFs are first parsed locally. If the document is scanned or an image, the application uses the configured `OPENAI_API_KEY` and `OPENAI_AADHAAR_MODEL` for document extraction. The default Aadhaar extraction model is `gpt-5.6-luna`.

## Render

Keep the existing Supabase Session Pooler `DATABASE_URL` in Render. The included `render.yaml` deliberately uses `sync: false` for DATABASE_URL and does not create a Render database.
