# Nimbus Jellyfin

A focused fork of [Nimbus](https://github.com/ivarbrandt/skin.nimbus) for **Kodi + Jellyfin for Kodi** on a TV / Android TV box.

The goal is deliberately narrow:

- straightforward remote-control navigation;
- direct access to Movies and TV Shows synchronized by Jellyfin for Kodi;
- clear poster browsing;
- prominent title, plot, ratings and runtime;
- Continue Watching and Recently Added widgets;
- minimal home-screen clutter.

## Status

This fork is currently being bootstrapped from upstream Nimbus `0.1.43`.

The add-on ID intentionally remains **`skin.nimbus`** so existing Nimbus helper integration continues to work. The display name is **Nimbus Jellyfin**.

See [JELLYFIN.md](JELLYFIN.md) for the intended Kodi/Jellyfin setup.

## Development plan

1. Reproducible installable ZIP build.
2. Jellyfin-oriented home-screen preset.
3. Movie and TV browsing defaults optimized for a D-pad remote.
4. TV testing on Kodi Omega.
5. Optional self-hosted Kodi repository for one-URL installation and updates.

## Upstream and license

Original Nimbus by **Ivar Brandt**:
https://github.com/ivarbrandt/skin.nimbus

Nimbus code is licensed under **GPL-2.0**. Nimbus artwork is licensed under **CC BY-SA 4.0**. See [LICENSE.txt](LICENSE.txt).

This fork is not affiliated with the Jellyfin project.
