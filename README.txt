Livenza Back Office Web - Review QR Fix v1.1

Upload these files/folders to the ROOT of the existing GitHub livenza-backoffice-web repository and choose to replace files with the same names:
- app.py
- requirements.txt
- templates/reviews.html
- static/app.js
- static/style.css

The Supabase database migration adding review.google_review_url has already been applied.
Render should auto-deploy after commit. If not, choose Manual Deploy -> Deploy latest commit.

New Review Generator features:
- Google Review Link field
- Saved default Google review link
- Visible scannable QR code
- Open Google Review Page button
- Download QR button
- Copy Review + Open Google button
- Google review link stored with each review draft

Google does not allow third-party sites to pre-fill the review text in the Google review form. The combined button copies the review text to clipboard and opens the Google review page, where the customer pastes it.
