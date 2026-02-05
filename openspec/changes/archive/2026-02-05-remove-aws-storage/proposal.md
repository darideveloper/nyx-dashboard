# Proposal: Remove AWS Storage Integration

## Why

The project currently has conditional logic for AWS S3 which adds unnecessary complexity and external dependencies. Since deployments on Coolify can utilize persistent volumes, local filesystem storage is sufficient and more cost-effective.

## What Changes

- Remove `django-storages` and `boto3` from `requirements.txt`.
- Delete custom AWS storage backend implementations in `nyx_dashboard/storage_backends.py`.
- Consolidate storage configuration in `nyx_dashboard/settings.py` to always use the local filesystem.
- Clean up unused AWS environment variables from `.env` files.
