# Capability: Local File Storage

This capability ensures that all file operations (static and media) are handled exclusively by the local filesystem.

## ADDED Requirements

### Requirement: Default Local Storage
The system MUST use the local filesystem for all file storage.

#### Scenario: Media File Upload
- **Given** a model with an `ImageField` (e.g., `blog.Image`).
- **When** a user uploads an image file.
- **Then** the file MUST be saved in the `MEDIA_ROOT` directory on the local disk.
- **And** the file URL MUST start with `MEDIA_URL` (typically `/media/`).

#### Scenario: Static File Serving
- **Given** static assets in the `static/` directory.
- **When** `collectstatic` is run.
- **Then** files MUST be collected into `STATIC_ROOT`.
- **And** WhiteNoise MUST serve these files with compression and manifest support.
