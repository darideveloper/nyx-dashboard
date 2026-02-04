# Project Context

## Purpose
Nyx Dashboard is a Django-based administrative and management platform designed for e-commerce and affiliate operations. It manages users, store items, affiliates, and provides a backend for a landing page. It integrates with payment gateways like Stripe and PayPal and uses AWS S3 for media storage.

## Tech Stack
- **Languages:** Python 3.12, SASS/CSS, HTML, JavaScript
- **Framework:** Django 4.2.7
- **Admin Interface:** Jazzmin
- **Database:** PostgreSQL (Production), SQLite (Development/Testing)
- **Web Server:** Gunicorn 20.1.0, WhiteNoise 6.2.0
- **Storage:** AWS S3 (django-storages + boto3)
- **Payments:** Stripe, PayPal
- **Testing:** Selenium, Django Test Framework
- **Infrastructure:** Docker, CapRover

## Project Conventions

### Code Style
- Follows standard Python PEP 8 guidelines.
- Uses `django-style` coding conventions.
- SASS is used for styling custom admin elements.

### Architecture Patterns
- **Monolithic Architecture**: Standard Django project structure.
- **Modular Apps**: Functionality divided into distinct apps:
    - `core`: Core functionalities.
    - `user`: User management and authentication.
    - `store`: E-commerce specific logic (products, sales).
    - `affiliates`: Affiliate management system.
    - `landing`: Landing page management.
- **Environment Configuration**: Heavily relies on `.env` files (`.env`, `.env.prod`, `.env.testing`) for configuration.

### Testing Strategy
- **Unit/Integration Tests**: Standard Django tests.
- **End-to-End (E2E) Tests**: Uses Selenium (`selenium`) for browser automation, with support for headless mode via environment variables (`TEST_HEADLESS`).
- **Database**: Uses a separate `testing.sqlite3` database for tests.

### Git Workflow
- Standard Git workflow (Feature Branch Workflow recommended).
- `master`/`main` as the production branch.

## Domain Context
- **E-commerce**: Handling of products (`store` app), sales, and inventory.
- **Affiliate Marketing**: Tracking commissions and affiliates.
- **Deployment**: The application is containerized using Docker and designed to be deployed via CapRover.

## Important Constraints
- **Localization**: Spanish (`es_ES`) locale is configured in the Dockerfile.
- **Timezone**: configured to `Europe/Madrid`.

## External Dependencies
- **AWS S3**: For static and media file storage.
- **Stripe API**: For processing payments.
- **PayPal API**: For processing payments.
- **Mail/SMTP**: Email sending capabilities configured via environment variables.
