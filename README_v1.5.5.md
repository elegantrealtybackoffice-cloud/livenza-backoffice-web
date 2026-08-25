# Livenza Life Operations Cloud — Web 1.5.5

Web 1.5.5 turns the login mascot into a persistent, useful and playful Livenza Live Companion.

## Persistent mascot

- The existing full-screen welcome and dance still plays once after every successful login.
- When the welcome finishes, the mascot settles at the edge of the website and remains available across authenticated modules.
- It performs brief wave, hop, peek, wobble and celebration routines at spaced intervals.
- A speech card rotates through the current weather, tenant/vacancy/earning updates and motivational thoughts without covering the workspace continuously.
- Floating stars and light points use a restrained generative motion language inspired by the supplied Squarespace Design Intelligence page.

## Live companion panel

Click the mascot to open a translucent panel containing:

- Current temperature, condition, feels-like temperature, humidity and wind.
- Four-day high/low and precipitation forecast.
- Switches for Gurugram, Jaipur, Delhi, Mumbai and Bengaluru.
- Current tenants, vacant beds, food earnings and hot queries.
- Rotating motivational thoughts.
- A manual Replay Weather Scene action.

Weather is supplied by Open-Meteo and cached for ten minutes. Network failures do not block page use, operational data or quotes.

## Weather-responsive UI

The website can briefly display rain, storm, cloud, fog, snow, sunlight or night effects based on the current condition. The scene fades automatically after 7–20 seconds and is remembered for a three-hour weather window so normal navigation does not repeatedly trigger it. Reduced-motion mode suppresses all weather particles.

## Admin controls

Settings → Livenza Live Companion can control:

- Side mascot visibility.
- Weather forecast.
- Temporary weather scenes.
- Operational updates.
- Motivational quotes.
- Default city.
- Weather-scene duration.

No database migration is required because these preferences use the existing Settings table. `WEATHER_LATITUDE` and `WEATHER_LONGITUDE` are optional environment overrides for the configured default city.

After deployment, confirm `/version` returns `Web 1.5.5` and includes `persistent-live-mascot`, `live-weather-forecast`, `transient-weather-scenes` and `floating-star-motion`.
