# Design: Local Filesystem Storage Consolidation

The project currently uses a conditional storage system. This design focuses on removing the branching logic and standardizing on the local filesystem.

## Current Architecture
- `nyx_dashboard/settings.py` checks `STORAGE_AWS`.
- If `True`: Uses `nyx_dashboard.storage_backends.PublicMediaStorage` etc.
- If `False`: Uses `django.core.files.storage.FileSystemStorage`.

## Proposed Architecture
- Remove `STORAGE_AWS` dependency.
- Define a single `STORAGES` configuration that uses:
    - `FileSystemStorage` for default/media.
    - `CompressedManifestStaticFilesStorage` (WhiteNoise) for staticfiles.
- Standardize `STATIC_ROOT` and `MEDIA_ROOT` paths.

## Persistent Storage in Coolify
For production deployments on Coolify, the `media/` directory must be mapped to a persistent volume in the Docker container/compose setup. This ensures uploaded files persist across redeployments.

## Cleanup
1.  **Dependencies**: Uninstalling `django-storages` and `boto3` reduces the attack surface and image size.
2.  **Code**: Deleting `nyx_dashboard/storage_backends.py` removes dead code once the settings are updated.
3.  **Environment**: Removing AWS keys from `.env` files prevents leakage of unused credentials.
