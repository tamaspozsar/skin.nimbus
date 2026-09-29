# Jellyfin setup

Nimbus Jellyfin is intended for a Kodi installation where **Jellyfin for Kodi** synchronizes the Jellyfin libraries into Kodi's native video library.

## Recommended client mode

Use **Add-on mode** in Jellyfin for Kodi unless the TV box has direct and stable SMB/NFS access to the media paths.

## Library model

After Jellyfin for Kodi has completed its initial sync, Kodi should expose the synchronized content through its native library nodes:

- Movies
- TV Shows
- Recently Added
- In Progress / Continue Watching

Nimbus Jellyfin will target these native Kodi nodes rather than browsing inside the Jellyfin add-on UI.

## First test

Before changing the skin, verify in Kodi's default skin that:

1. Movies contains the Jellyfin-synchronized films.
2. TV Shows contains the Jellyfin-synchronized series.
3. At least one item opens and plays.
4. Watched/resume state is synchronized with Jellyfin.

If those work, any remaining issue is skin/navigation related rather than Jellyfin connectivity.

## Packaging

The GitHub Actions workflow produces an installable `skin.nimbus-<version>.zip` artifact.

Nimbus also requires `script.nimbus.helper`. The packaging workflow additionally downloads and packages the current upstream helper so a test device can install the helper ZIP first if dependency resolution is not available from another configured Kodi repository.

A self-hosted Kodi repository is planned after the TV-tested skin preset is stable.
