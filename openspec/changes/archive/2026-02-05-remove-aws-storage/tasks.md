# Tasks: Remove AWS Storage Integration

- [x] **Dependency Cleanup**
    - Remove `django-storages` and `boto3` from `requirements.txt`.
    - Validate that no other packages depend on these (not expected).

- [x] **Code Deletion**
    - Delete `nyx_dashboard/storage_backends.py`.

- [x] **Settings Refactoring**
    - Remove `STORAGE_AWS = os.environ.get("STORAGE_AWS") == "True"` from `nyx_dashboard/settings.py`.
    - Remove the entire `if STORAGE_AWS:` block.
    - Consolidate `STATIC_ROOT`, `MEDIA_ROOT`, `STATIC_URL`, `MEDIA_URL` and `STORAGES` at the top level of the storage section.
    - Ensure `whitenoise.storage.CompressedManifestStaticFilesStorage` is used for `staticfiles`.

- [x] **Environment Cleanup**
    - Remove `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, and `STORAGE_AWS` from `.env.dev`.
    - Remove the same variables from `.env.prod`.

- [x] **Verification**
    - Run `python manage.py check` to ensure no configuration errors.
    - Run `python manage.py collectstatic --no-input` to verify static file handling.
    - Verify that file uploads in the admin (e.g., Blog images) still work and save to the local `media/` directory.
