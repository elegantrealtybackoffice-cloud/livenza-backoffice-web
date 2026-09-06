# Livenza.fit Music, Video & Live Integration Architecture

## Offline audio

The supplied application already supports local audio files with the browser's file and audio APIs. Local tracks are not uploaded by the app. The workout counter continues independently if audio fails.

## Music search and playback

### Spotify

The standalone build uses a provider search/deep-link rather than embedding Spotify playback. Spotify's current Web Playback SDK can create a browser Spotify Connect player, but its documentation includes account and policy requirements and explicitly states commercial-use restrictions. Livenza.fit should not ship commercial in-app Spotify streaming unless Spotify has approved the intended use and the integration complies with current developer terms.

Official references:
- https://developer.spotify.com/documentation/web-playback-sdk
- https://developer.spotify.com/documentation/web-playback-sdk/tutorials/getting-started

### Apple Music

MusicKit on the Web supports Apple Music playback in a browser with Apple developer configuration and user authentication. A production Livenza.fit adapter can use MusicKit after creating the required media identifier/private key and server-signed developer-token flow.

Official reference: https://developer.apple.com/musickit/

### YouTube Music

The first release treats YouTube Music as a search/deep-link destination. Do not claim an in-app YouTube Music streaming integration without a provider-supported playback/licensing path for the intended product.

## Voice counting and media ducking

Local-file playback can be ducked during spoken rep counts by reducing the local `HTMLAudioElement.volume`, then restoring it after speech ends. Connected streaming providers may impose restrictions on altering or synchronizing their content; provider policy always overrides Livenza.fit convenience behavior.

## Recorded workout videos

Recommended production path:

```text
Trainer upload
  -> private/original object storage
  -> transcoding/CDN provider
  -> signed/public playback manifest according to content policy
  -> Livenza.fit video catalog metadata
```

Video records should contain title, trainer, duration, level, target category, poster image, playback id, published state, captions/subtitles and safety notes.

## Live classes

Live classes should use an adapter that provides:

- scheduled session id and start/end time;
- trainer/host identity;
- capacity and enrollment;
- join authorization;
- optional recording handoff;
- chat/moderation controls;
- cancellation/reschedule status.

The web client must receive short-lived join material from the backend, not long-lived provider secrets.

## AI / natural-language music intent

A phrase such as "play high-energy chest-day music" should be resolved into a structured intent:

```json
{
  "activity": "strength",
  "energy": "high",
  "genre": null,
  "explicit_content": "profile_default",
  "provider": "user_default"
}
```

The music adapter then searches an approved provider or chooses a curated Livenza playlist. The AI layer does not bypass provider authentication, subscriptions or licensing.
