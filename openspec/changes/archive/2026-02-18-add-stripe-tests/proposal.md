# Proposal: Add Stripe Integration Tests

## Summary
Expand the existing test suite to include comprehensive coverage for the Stripe payment provider. Currently, the codebase has a multi-provider system, but the tests are almost exclusively focused on PayPal. This proposal introduces a refactored testing structure that enables high-parity testing for both PayPal and Stripe, including live checkout simulations.

## Problem Statement
The Stripe integration lacks automated tests for the following:
- Generation of Stripe checkout links.
- Payment confirmation via `SaleDoneView`.
- Correct invoice generation with Stripe-specific commissions.
- Selenium integration tests for the Stripe checkout flow.
- Support for switching providers at the test level without manual `.env` changes.

## Proposed Solution
1. **Refactor Payment Tests**:
    - Identify tests in `store/tests/test_views.py` that are provider-specific (e.g., `test_sale_no_logo` asserting `paypal.com` in link).
    - Extract common logic into methods in `store/tests/payment_base.py`.
    - Create `SaleViewTestMixin` that uses dynamic assertions based on `self.payment_provider`.
2. **Provider Parity**:
    - Implement `SaleViewStripeTest` inheriting from `SaleViewTestMixin` and `TestCase`.
    - Apply `@override_settings(PAYMENT_PROVIDER='stripe')` to the class.
    - Implement specific assertions for Stripe links (prefix `checkout.stripe.com`) and invoice content.
    - Refactor `SaleDoneViewTest` into `SaleDoneViewTestMixin` in `store/tests/payment_base.py`.
    - Create `SaleDonePaypalTest` and `SaleDoneStripeTest` subclasses to handle provider-specific invoice commission and checkout logic.
3. **Dynamic Settings**:
    - Ensure `get_payment_provider` logic in `utils/payment_provider.py` respects the overridden setting during tests.
    - No changes needed to `utils/payment_provider.py` itself if `override_settings` is used correctly, as checks `settings.PAYMENT_PROVIDER`.
4. **Mocking/Sandbox**:
    - For `StripeCheckout.get_checkout_link`, mock `stripe.checkout.Session.create` to return a dummy URL and Session ID during unit tests to avoid API calls.
    - For `StripeCheckout.is_payment_done`, mock `stripe.checkout.Session.retrieve`.
    - For `SaleViewTestLive`:
        - Create a `StripePaymentPage` object (Page Object Pattern) to handle Stripe's DOM interactions.
        - Use standard test card numbers (e.g., `4242...`) for the live test.

## Risks & Mitigations
- **Selenium Complexity**: Stripe checkout pages are dynamic and may change. *Mitigation*: Focus heavily on unit tests for link generation and success redirection, using Selenium primarily for smoke testing the handshake.
- **Provider Credentials**: Stripe secret keys must be present in the test environment. *Mitigation*: Use `.env.testing` for safe test keys.
