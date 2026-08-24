# Livenza Back Office Web 1.4.8

## Home AI core
- Replaces LIVE / ONLINE text disc with the Livenza logo.
- Animated light runs continuously around the logo border.
- Orbiting status dots, halo pulse, logo sheen and subtle spark effects.
- Additional professional ambient sweeps across hero, metrics and module cards.

## Food Delivery Hub integrations
- New Integrations workspace for Swiggy, Zomato, Toing and other partners.
- Official partner website links pre-seeded.
- Restaurant/outlet ID and account reference fields.
- Inbound webhook URL for automatic order feeds.
- Generic approved-API pull connector with Render ENV references for bearer tokens / API keys.
- Sync state, last sync time and record counts.
- Order webhook parser supports single orders or lists under orders/data/items/records/results.
- Upserts matching platform + order ID to reduce duplicates.

## Live Partner Websites
- New Food Hub tab embeds each configured restaurant partner website in an Operations Cloud browser panel.
- Direct Open in New Tab fallback for partner sites that block iframe embedding.
- Passwords and OTPs stay on official partner websites and are never stored by Livenza.

## Official URLs seeded
- Swiggy Restaurant Partner: https://partner.swiggy.com/v2/
- Swiggy Developer Portal: https://developers.swiggy.com/login
- Zomato Restaurant Partner: https://www.zomato.com/partners
- Zomato Merchant App: https://www.zomato.com/business/merchant-app
- Toing: https://www.toingit.com/

## Important
A portal link is live immediately. Automatic order ingestion requires the delivery partner to provide a webhook or approved API access. Public restaurant-partner order APIs are not assumed or fabricated.
