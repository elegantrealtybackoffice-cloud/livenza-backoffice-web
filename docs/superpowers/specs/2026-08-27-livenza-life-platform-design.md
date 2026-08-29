# Livenza.life Platform — Approved Product & Technical Design

**Date:** 2026-08-27  
**Status:** Approved design consolidated from Sections 1–7  
**Scope:** Livenza.life master brand website, Livenza.stays, Livenza.store, My Livenza, Livenza+, shared platform architecture, visual system, deployment blueprint, and Version 1 release criteria.

## 1. Executive Summary

Livenza.life is the master lifestyle brand. The platform must not present Livenza as only a hostel, hotel, or accommodation company. The product architecture is a single customer ecosystem spanning accommodation, commerce, fitness, grooming, skincare, and media, with Livenza.stays and Livenza.store as the first fully operational commercial verticals.

The platform uses one customer identity, one customer profile, one loyalty layer, and one authoritative operational data model. The public consumer experience is separated from the staff back-office experience, but both are connected through shared domain logic and a common PostgreSQL source of truth.

The Version 1 success definition is simple: a customer can discover Livenza, book a stay, pay, receive confirmation, access the booking in My Livenza, buy store products with the same identity, earn Livenza+ benefits, and have those transactions appear correctly in the Livenza back-office.

## 2. Locked Brand Architecture

### 2.1 Master brand

**Livenza.life** — the umbrella lifestyle identity.

### 2.2 Sub-brands

- **livenza.stays** — student living, hostels, corporate living, hotels, short stays.
- **livenza.fit** — gyms, fitness, yoga, wellness.
- **livenza.store** — apparel, merchandise, room, travel, and lifestyle products.
- **livenza.groom** — grooming and personal care.
- **livenza.skin** — skincare and beauty.
- **livenza.media** — creative, social, branding, media, and future creator services.

### 2.3 Launch status

- `livenza.stays` — fully operational in Version 1.
- `livenza.store` — fully operational in Version 1.
- `.fit`, `.groom`, `.skin`, `.media` — polished ecosystem pages and early-access capture, not full operational platforms in Version 1.

### 2.4 Brand-domain strategy

Use visible sub-brand nomenclature while keeping the initial web platform consolidated under the master domain:

- `livenza.life/stays`
- `livenza.life/store`
- `livenza.life/fit`
- `livenza.life/groom`
- `livenza.life/skin`
- `livenza.life/media`

This preserves brand cohesion, simplifies customer identity, and avoids early SEO and operational fragmentation.

## 3. Master Website Information Architecture

### 3.1 Primary sitemap

```text
LIVENZA.LIFE
├── Home
├── Explore Livenza
│   ├── livenza.stays
│   ├── livenza.fit
│   ├── livenza.store
│   ├── livenza.groom
│   ├── livenza.skin
│   └── livenza.media
├── Cities
│   ├── Jaipur
│   ├── Gurugram
│   └── Future Cities
├── Life at Livenza
│   ├── Community
│   ├── Food
│   ├── Fitness
│   ├── Events
│   ├── Work & Study
│   └── Stories
├── About
│   ├── Our Story
│   ├── The Livenza Standard
│   ├── Leadership / Administration
│   ├── Partners
│   └── Careers
├── Journal
├── Partner With Us
├── Contact
├── My Livenza
└── Book / Shop
```

### 3.2 Homepage sequence

1. Hero — `LIVE MORE.`
2. Livenza universe — six sub-brand cards.
3. Livenza.stays — accommodation discovery.
4. City explorer — Jaipur and Gurugram at launch.
5. Selected properties.
6. Life at Livenza — food, fitness, community, study, work, events.
7. Livenza.store — lifestyle commerce.
8. Emerging brands — `.fit`, `.groom`, `.skin`, `.media`.
9. The Livenza Standard.
10. Real resident/social proof.
11. Closing master-brand statement.
12. Minimal premium footer.

### 3.3 Master positioning

The homepage must not resemble a generic OTA or hostel website. Accommodation appears as one part of a broader lifestyle ecosystem.

## 4. Livenza.stays Product Design

### 4.1 Shared booking engine, tailored entry paths

Use one booking engine with three intent-specific user journeys:

- Student Living
- Corporate Living
- Short Stays

Do not create three separate booking databases or three incompatible booking systems.

### 4.2 Student flow

```text
City / College
→ Move-in / Academic Period
→ Gender / Eligibility Rules
→ Room Type
→ Property Results
→ Room Category
→ Add-ons
→ Customer + Guardian Details
→ Booking Summary
→ Payment / Reservation
→ Confirmation
```

### 4.3 Corporate flow

```text
City / Office / Landmark
→ Move-in
→ Duration
→ Number of Residents
→ Studio / Apartment / Unit Type
→ Services
→ Individual Booking or Corporate Enquiry
```

### 4.4 Short-stay flow

```text
Destination
→ Check-in
→ Check-out
→ Guests
→ Available Stays
→ Unit / Room
→ Extras
→ Payment
→ Instant Confirmation
```

### 4.5 Search inputs

The stays search must understand:

- city;
- area;
- college/university;
- corporate hub/office landmark;
- Livenza property name.

### 4.6 Property page contract

Every live property must include:

- hero/gallery;
- location;
- stay type;
- room categories;
- verified pricing;
- verified availability state;
- amenities;
- food information;
- safety information;
- transport where relevant;
- policies;
- reviews where verified;
- FAQs;
- book/enquire CTA.

Incomplete properties must not appear in public search.

### 4.7 Inventory hierarchy

```text
City
→ Property
→ Building / Wing
→ Floor
→ Unit / Room
→ Bed
```

Version 1 may allocate specific inventory internally after a customer selects a room category. Customer-selectable individual bed maps are deferred.

### 4.8 Booking modes

Support:

- **Book Now** — customer pays the configured amount and confirms.
- **Reserve** — customer pays a configured reservation amount for a configured validity period.

Reservation rules must be configurable in admin, not hard-coded globally.

### 4.9 Parent Share

Student bookings must support a secure `Share with Parent` experience containing:

- property;
- room category;
- pricing;
- meals;
- safety;
- transport;
- amenities;
- policies;
- booking summary;
- `Approve & Pay` continuation.

### 4.10 Add-ons

Version 1 add-ons may include:

- laundry;
- transport;
- bedding;
- Move-In Kit;
- other property-specific optional services.

## 5. Livenza.store Product Design

### 5.1 Positioning

Livenza.store is a premium lifestyle label, not institutional hostel merchandise.

Primary storefront worlds:

- Wear
- Move
- Live
- Accessories / Travel
- Limited / Collaborations
- Resident Exclusives

### 5.2 Version 1 catalogue

Launch with approximately 15–25 curated SKUs rather than a large low-quality catalogue.

Suggested first collection:

- signature oversized T-shirt;
- premium regular-fit T-shirt;
- polo;
- hoodie;
- training T-shirt;
- training shorts;
- cap;
- tote;
- gym bag;
- bottle;
- tumbler;
- mug;
- bedsheet set;
- bath towel;
- laundry bag;
- backpack;
- umbrella;
- Move-In Essential Kit.

### 5.3 Store experience

Required Version 1 features:

- editorial store homepage;
- collections and categories;
- product pages;
- variants and sizes;
- stock state;
- cart;
- checkout;
- order confirmation;
- My Livenza order history;
- resident delivery option where operationally supported;
- property pickup/delivery where configured.

### 5.4 Move-In Kits

Move-In Kits must be purchasable from the store and offerable inside the stay-booking flow.

This is a deliberate cross-brand revenue feature and a visible proof of the Livenza ecosystem concept.

## 6. My Livenza & Livenza ID

### 6.1 Core principle

**One Person. One Livenza ID.**

A customer creates one identity and reuses it across every Livenza vertical.

### 6.2 Primary customer authentication

Version 1 should use passwordless login as the primary consumer experience:

- mobile number + OTP;
- verified email support;
- passkeys may be added when the identity layer is ready.

Long forms must not block browsing or product discovery.

### 6.3 My Livenza modules — Version 1

- Home
- My Stay
- Payments
- Documents
- Store Orders
- Livenza+
- Support
- Profile

Modules should be contextual. Store-only customers should not be forced through irrelevant resident screens.

### 6.4 Progressive customer profile

The customer record grows as services are used:

**Basic:** name, mobile, email, DOB where required.  
**Stay:** college/employer, guardian, KYC, address.  
**Commerce:** delivery addresses, sizes, product preferences.  
**Future verticals:** only collect data needed for the relevant service.

## 7. Livenza+ Loyalty

### 7.1 Version 1 scope

Livenza+ launches as a free unified loyalty identity.

Version 1 shows:

- membership status;
- points balance;
- points history;
- basic eligible rewards.

### 7.2 Initial earning sources

- eligible stay bookings;
- eligible store purchases;
- eligible referrals.

The exact earning and redemption economics remain admin-configurable business rules rather than fixed code constants.

### 7.3 Deferred loyalty capabilities

- paid membership;
- complex tier ladder;
- general-purpose cash wallet;
- large reward marketplace.

## 8. Unified Customer & Domain Model

### 8.1 Customer model

Do not create separate customer tables per sub-brand.

```text
CUSTOMER
├── identities
├── addresses
├── preferences
├── consents
├── bookings
├── stays
├── orders
├── payments
├── loyalty
├── documents
└── support tickets
```

### 8.2 Staff identities

Staff/admin identities are operational identities with separate access controls and stronger security rules.

Role examples:

- Super Admin
- Finance
- Property Manager
- Front Desk
- Store Manager
- Sales
- Marketing
- Support

### 8.3 Backend domains

Version 1 backend should be modularised around:

```text
identity
customers
properties
inventory
bookings
commerce
orders
payments
loyalty
memberships
services
documents
support
notifications
content
integrations
admin
audit
```

## 9. Existing Back-Office Baseline & Migration Constraint

The current operational application is a Flask + Flask-SQLAlchemy system with PostgreSQL support and SQLite fallback, and it already contains operational entities such as users, cities, rooms, and tenants. Existing back-office work has also established a requirement to preserve working Flask routes, permissions, data workflows, and integrations while improving the application around them.

Therefore Version 1 must **not** attempt a destructive full rewrite of the back-office.

Instead:

1. preserve the operational application;
2. extract or reorganise reusable domain logic behind APIs/modules;
3. add new customer, booking, commerce, and loyalty models in a controlled migration;
4. progressively make the new Livenza platform the authoritative source of truth;
5. use integration adapters for legacy/third-party systems during transition.

## 10. Technical Architecture

### 10.1 Recommended architecture

Use a hybrid architecture:

- **Consumer frontend:** Next.js / React.
- **API and operational domain layer:** Flask / Python.
- **Back-office:** existing Flask application, progressively modularised.
- **Database:** PostgreSQL as the authoritative production store.
- **Media/documents:** S3-compatible object storage or equivalent private/public object storage.

### 10.2 Target topology

```text
Users
  ↓
livenza.life — Next.js
  ↓
api.livenza.life — Flask API/domain layer
  ↓
PostgreSQL — authoritative data
  ↑
backoffice.livenza.life — operational/admin experience
```

### 10.3 Architecture style

Use a **modular monolith**, not microservices, for Version 1.

Rationale:

- simpler deployment;
- simpler transactions;
- easier debugging;
- compatible with the current Flask application;
- easier migration;
- still provides strong internal boundaries if domains are separated properly.

### 10.4 API principle

The consumer frontend must not query database tables directly. It communicates through versioned API/domain contracts.

Example API surface:

```text
/api/v1/me
/api/v1/me/stays
/api/v1/me/orders
/api/v1/me/payments
/api/v1/me/documents
/api/v1/me/rewards
/api/v1/me/support
/api/v1/cities
/api/v1/properties
/api/v1/availability
/api/v1/bookings
/api/v1/products
/api/v1/cart
/api/v1/orders
/api/v1/payments
```

## 11. Booking & Inventory Domain

### 11.1 Rate plans

The booking engine must support multiple stay models without separate systems:

- nightly;
- weekly;
- monthly;
- semester;
- academic year;
- corporate contract.

### 11.2 Booking record

```text
BOOKING
├── customer
├── property
├── inventory allocation
├── stay type
├── start date
├── end date / duration
├── rate plan
├── deposit
├── add-ons
├── discounts
├── payment status
└── booking status
```

### 11.3 Inventory hold and double-booking prevention

Flow:

```text
AVAILABLE
→ TEMPORARY HOLD
→ PAYMENT
→ CONFIRMED
```

If the hold expires or payment fails, inventory returns to `AVAILABLE`.

The exact hold duration is configuration, not a hard-coded universal business rule.

Database constraints/transactions must prevent two simultaneous payment flows from confirming the same inventory.

## 12. Payments

### 12.1 Version 1 requirements

Support:

- UPI;
- cards;
- netbanking;
- booking payments;
- reservation amounts;
- security deposits where configured;
- store orders;
- refunds and partial refunds.

### 12.2 Payment authority

The frontend never decides that a payment is successful.

Expected flow:

```text
Customer starts payment
→ Livenza creates internal payment/order
→ Gateway checkout
→ Gateway callback/webhook
→ Backend verifies signature/state
→ Internal payment updated
→ Booking/order confirmed
```

### 12.3 Payment state model

```text
Created
Pending
Paid
Failed
Refunded
Partially Refunded
```

### 12.4 Idempotency

Duplicate payment webhooks must not duplicate bookings, receipts, inventory changes, or loyalty credits.

External events require idempotent processing and a processed-event record/key.

## 13. Content & Commerce Administration

### 13.1 Content Studio

Marketing/admin users should be able to manage:

- homepage campaigns;
- city pages;
- property descriptions;
- amenities;
- galleries;
- FAQs;
- offers;
- store collections;
- products;
- journal posts;
- SEO metadata.

Content edits should not require source-code changes.

### 13.2 Property Admin

Required controls:

- properties;
- buildings/wings;
- floors;
- units/rooms;
- beds;
- room categories;
- amenities;
- pricing;
- inventory availability;
- images;
- policies.

### 13.3 Booking Admin

Required controls:

- booking search;
- customer search;
- property filter;
- stay dates;
- booking status;
- payment status;
- inventory assignment;
- notes;
- cancellation;
- refund state.

Money-affecting actions require audit logging.

### 13.4 Store Admin

Required controls:

- products;
- variants;
- inventory/stock;
- collections;
- orders;
- fulfilment;
- cancellation;
- returns/refunds.

## 14. Integrations

The existing central Integrations Center remains the canonical home for third-party configuration and integration status.

Consumer/domain modules call integration adapters; they do not each create separate credential stores.

Integration categories may include:

- payments;
- WhatsApp;
- email;
- Google Drive;
- maps;
- AI;
- Rentok/legacy operations;
- food platforms;
- banking;
- electricity;
- webhooks.

Secrets must remain outside source code and must not be exposed in frontend payloads or audit logs.

## 15. Notifications

Use one notification domain driven by events rather than hard-coded communication inside every module.

Example events:

```text
booking.confirmed
reservation.expiring
payment.received
payment.due
order.confirmed
order.shipped
support.updated
reward.earned
movein.approaching
```

Initial transactional channels:

- email;
- WhatsApp where configured.

Future channels may include SMS, in-app, and push.

## 16. Documents & Media

### 16.1 Public assets

Property images, product images, campaign media, and public video may use public/CDN-backed object storage.

### 16.2 Private assets

KYC, agreements, receipts containing private information, and customer uploads must use private storage with authorised, expiring access.

Do not store long-term customer files directly on ephemeral application-server filesystems.

## 17. Visual Design System

### 17.1 Brand character

The system must feel:

- premium;
- youthful;
- bold;
- clean;
- urban;
- confident;
- lifestyle-first.

It must avoid:

- generic hostel aesthetics;
- generic hotel OTA layouts;
- corporate real-estate styling;
- childish Gen-Z iconography;
- excessive visual effects.

### 17.2 Visual principle

**One brand system, different personalities.**

The `Livenza` wordmark remains stable. The suffix and accent system carry the vertical personality.

### 17.3 Accent directions

- `.life` — electric violet.
- `.stays` — deep azure.
- `.fit` — acid/high-energy lime.
- `.store` — tangerine/burnt orange.
- `.groom` — deep burgundy.
- `.skin` — warm coral/blush.
- `.media` — electric cyan.

The majority of UI remains neutral. Accent colour is used selectively for navigation state, CTA emphasis, small surfaces, transitions, and brand moments.

### 17.4 Typography

Use:

- bold editorial display typography for marketing/campaigns;
- neutral, highly readable interface typography for booking, forms, checkout, account, and admin.

Do not redistribute proprietary Apple font files.

### 17.5 Motion

Motion must be purposeful and performance-conscious:

- subtle image parallax where valuable;
- typography reveals;
- image crossfades;
- controlled hover scale;
- brand-accent transitions;
- short interface transitions.

Avoid:

- constant floating/bouncing;
- heavy WebGL as a general page dependency;
- animations that block booking, search, cart, or checkout;
- full-page blur effects.

### 17.6 Photography

Prefer real Livenza properties, real residents, real activities, real products, and real city context.

Avoid generic stock imagery and imagery that looks artificially luxurious or AI-generated.

### 17.7 Mobile-first rule

Mobile is the primary transactional experience.

Required patterns:

- large tap targets;
- sticky booking/add-to-bag actions;
- swipeable galleries;
- minimal form depth;
- fast UPI-oriented checkout;
- strong WhatsApp sharing;
- lightweight media delivery.

## 18. Performance & Accessibility

### 18.1 Performance

The consumer site must remain lightweight even when visually rich.

Required practices:

- responsive images;
- lazy loading below the fold;
- compressed short video;
- route-level code splitting;
- minimal third-party scripts;
- server-rendered/indexable editorial pages;
- no unnecessary global JavaScript;
- no large animation library unless it provides clear user value.

### 18.2 Accessibility

Version 1 requires:

- keyboard navigation;
- visible focus states;
- proper form labels;
- semantic headings;
- readable contrast;
- useful alt text;
- touch-size controls;
- reduced-motion support;
- clear validation/error messaging.

## 19. SEO & Analytics

### 19.1 SEO

Required:

- server-rendered/indexable city and property pages;
- canonical URLs;
- XML sitemap;
- robots configuration;
- Open Graph metadata;
- unique page titles/descriptions;
- product/property structured data where appropriate;
- image alt text;
- fast pages.

### 19.2 Analytics events

At minimum track:

```text
homepage_view
stays_search
property_view
availability_check
room_select
booking_start
parent_share
booking_payment_start
booking_complete
store_view
product_view
add_to_cart
checkout_start
purchase
signup
login
support_request
```

Analytics must help identify commercial funnel friction, not merely count page views.

## 20. Security Baseline

Production release is blocked without:

- HTTPS-only production traffic;
- secure HTTP-only session/auth cookies where used;
- CSRF controls where relevant;
- OTP throttling/rate limiting;
- input validation;
- strong staff role permissions;
- payment signature verification;
- secrets outside source code;
- authorised private-document access;
- audit logs for privileged actions;
- production database backups;
- safe migration/rollback procedures.

## 21. Environments & Deployment

### 21.1 Environments

Maintain separate:

- local;
- staging;
- production.

Suggested production domains:

- `livenza.life`
- `api.livenza.life`
- `backoffice.livenza.life`

Suggested staging:

- `staging.livenza.life`
- `api-staging.livenza.life`
- `backoffice-staging.livenza.life`

Staging must use a separate database and non-production integration credentials.

### 21.2 Deployment pipeline

```text
Code
→ Git repository
→ Automated tests
→ Build
→ Staging
→ Smoke / E2E tests
→ Production
→ Post-deploy production verification
```

A failed deployment must not replace the last known working release.

## 22. Version 1 Scope — Must Ship

### Master website

- Livenza.life homepage.
- Sub-brand ecosystem navigation.
- Jaipur and Gurugram city pages.
- Life at Livenza.
- About / story / standard.
- Contact / partner entry points.

### Livenza.stays

- Student Living.
- Corporate Living.
- Short Stay capability where live inventory exists.
- Search.
- Property pages.
- Room-category selection.
- Availability.
- Book Now.
- Reserve.
- Parent Share.
- Add-ons.
- Payment.
- Booking confirmation.

### My Livenza

- passwordless account creation/login;
- dashboard;
- My Stay;
- Payments;
- Documents;
- Store Orders;
- Livenza+ basic view;
- Support;
- Profile.

### Livenza.store

- 15–25 curated SKUs;
- Wear / Move / Live / Accessories;
- collections;
- product pages;
- variants;
- stock;
- cart;
- checkout;
- resident delivery where configured;
- Move-In Kits;
- order history.

### Admin/platform

- unified customer view;
- Property Admin;
- Booking Admin;
- Content Studio;
- Store Admin;
- Support management;
- payment records;
- audit-sensitive actions;
- analytics event collection;
- central integration adapters.

## 23. Explicit Version 1 Non-Goals

Do not make these launch blockers:

- full `.fit` membership system;
- `.groom` appointment engine;
- `.skin` full commerce rollout;
- `.media` creator/client portal;
- advanced Livenza+ tiers;
- general-purpose wallet;
- native iOS/Android app;
- customer-selectable graphical live bed map;
- complex enterprise corporate-contract engine;
- multi-brand mixed service cart;
- heavy 3D/WebGL site experience;
- universal AI concierge;
- destructive one-shot replacement of all existing back-office/legacy systems.

## 24. Version 1 Acceptance Journeys

### 24.1 Stay booking journey

This exact sequence must pass in production-like staging and again after production deployment:

```text
New User
→ Open livenza.life
→ Explore Stays
→ Search Jaipur
→ Open Property
→ Select Room Category
→ Enter Details
→ Add Move-In Kit
→ Pay
→ Booking Confirmed
→ My Livenza Created / Updated
→ Receipt Visible
→ Booking Visible in Back Office
→ Inventory Updated
```

### 24.2 Store journey

```text
Same Customer
→ Open Livenza.store
→ Open Product
→ Add to Bag
→ Checkout
→ Use Same Identity
→ Pay
→ Order Appears in My Livenza
→ Order Appears in Admin
→ Livenza+ Updated
```

### 24.3 Failure-path acceptance

Also verify:

- failed payment does not confirm booking/order;
- expired inventory hold becomes available again;
- duplicate webhook does not duplicate financial or loyalty effects;
- sold-out inventory cannot be purchased;
- unauthorized staff cannot access restricted customer/financial data;
- unavailable integrations degrade cleanly without breaking core booking/store flows.

## 25. Production Release Gates

Production launch requires all seven gates:

1. **Brand Gate** — approved visual identity implemented consistently.
2. **Functional Gate** — no dead primary navigation, booking, cart, account, or admin actions.
3. **Commercial Gate** — stay booking and store purchase complete end-to-end.
4. **Data Gate** — consumer and back-office show the same authoritative transaction/inventory/customer state.
5. **Payment Gate** — backend-verified payment flow and failure handling pass.
6. **Responsive Gate** — core journeys pass on phone, tablet, and desktop target browsers.
7. **Performance Gate** — no major loading lag, blocked interaction, menu lag, or blank-screen dependency on oversized JavaScript.

## 26. Implementation Sequence

After this design is approved as the written source of truth, implementation planning should follow this order:

1. platform/data foundation and migrations;
2. identity/customer model;
3. properties/inventory/content APIs;
4. consumer design system and master website shell;
5. Livenza.stays discovery and property pages;
6. booking/inventory hold/payment engine;
7. My Livenza;
8. Content/Property/Booking admin extensions;
9. Livenza.store catalogue/cart/order flow;
10. loyalty and cross-brand Move-In Kit integration;
11. analytics, SEO, accessibility, performance hardening;
12. migration/adapters for existing systems;
13. staging E2E validation;
14. production deployment and post-deploy verification.

## 27. Definition of Done

Livenza.life Version 1 is done only when it operates as one connected commercial platform, not a collection of visual pages.

A customer must be able to discover the master brand, complete a stay booking, pay, receive documentation, access the booking in My Livenza, buy Livenza.store products with the same identity, receive Livenza+ credit where applicable, and have the same authoritative transactions visible to the back-office team.

The platform must be fast, responsive, secure, maintainable, and designed so future `.fit`, `.groom`, `.skin`, and `.media` services plug into the same identity, payments, loyalty, content, and administrative foundations rather than becoming separate products.
