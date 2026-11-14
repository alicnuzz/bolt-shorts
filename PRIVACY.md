# Privacy Policy — Bolt Knows Why

_Last updated: November 15, 2026_

**Bolt Knows Why** ("the API Client") is a private publishing tool operated by Lochinbek Suyunov (contact: suyunovalicn@gmail.com). It uploads short videos that we create ourselves to our own YouTube channel, [@BoltKnowsWhy](https://www.youtube.com/@BoltKnowsWhy).

## Use of YouTube API Services
- This API Client uses **YouTube API Services**.
- By using this API Client you agree to be bound by the **YouTube Terms of Service**: https://www.youtube.com/t/terms
- Google's handling of data is described in the **Google Privacy Policy**: https://policies.google.com/privacy

## What data we access
- Using OAuth 2.0, the API Client accesses only the channel owner's own YouTube account, with two scopes: `youtube.upload` (to upload our own videos) and `youtube.readonly` (to read our own channel and video statistics).
- We do **not** access, collect, store, sell or share data of any other YouTube users or viewers.

## How data is used and stored
- The OAuth refresh token is stored only as an encrypted GitHub Actions secret and is used only by the channel owner's automated publishing job.
- Video titles, descriptions and the IDs of videos we uploaded are sent to the owner's private Telegram chat for approval and reporting. No other personal data is stored.
- We do not use cookies or any tracking, and we do not share any information with third parties.

## Deleting data and revoking access
- You can revoke this API Client's access at any time through the Google security settings page: https://myaccount.google.com/permissions
- When access is revoked, or on request to suyunovalicn@gmail.com, all stored API data (the OAuth token and any stored video IDs/statistics) is deleted within 7 days. Statistics read from the API are not kept longer than 30 days.

## Contact
Questions: suyunovalicn@gmail.com
