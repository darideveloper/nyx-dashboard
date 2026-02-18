# Design: Stripe Test Implementation

## Overview

The current test suite in `store/tests/test_views.py` and `store/tests/test_commands.py` is heavily coupled with PayPal-specific assertions and flows. To support Stripe tests with high parity, we will refactor the existing tests into a provider-agnostic structure and then execute them for each supported provider.

## Architectural Decisions

### 1. Test Parameterization

We will use a base class or a mixin pattern to define the core payment tests. This allows us to run the same logic twice:

- Once for **PayPal** (using `override_settings(PAYMENT_PROVIDER='paypal')`).
- Once for **Stripe** (using `override_settings(PAYMENT_PROVIDER='stripe')`).

### 2. Provider-Agnostic Assertions

We will replace hardcoded strings like `"paypal.com"` with dynamic checks. For example:

- `PAYPAL_LINK_PATTERN = "paypal.com/checkoutnow?token="`
- `STRIPE_LINK_PATTERN = "checkout.stripe.com/c/pay/"` (or similar depending on the local/test URL)

### 3. Selenium Selectors for Providers

The `LiveServerTestCase` classes will need a strategy for provider-specific selectors. Since Stripe Checkout is a separate hosted page, we will define a `get_provider_selectors()` method that returns the appropriate selectors and credentials for the active provider.

### 4. Switching Providers in Tests

We will add a mechanism to the test runner or a specific management command to easily switch between providers, or simply include both in the standard `python manage.py test` run.

## Proposed Changes

### 1. `store/tests/payment_test_mixin.py` (New File)

A mixin containing shared payment logic:

- `assertCheckoutLinkValid()`
- `mock_provider_payment()`
- `get_provider_credentials()`

### 2. `store/tests/test_views.py` Refactoring

- `SaleViewTest`: Split into `SaleViewPaypalTest` and `SaleViewStripeTest` (inheriting from a common base).
- `SaleViewTestLive`: Parameterize the `test_pay_sandbox_user` flow to handle Stripe's test card flow.

### 3. System Settings

Introduce `INVOICE_STRIPE_COMMISSION` in `settings.py` (matching the PayPal pattern) to ensure invoice generation tests are accurate for Stripe.
