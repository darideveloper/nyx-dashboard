# Proposal: Refactor Sale Live Tests

Refactor the `SaleViewTestLive` class in `store/tests/test_views.py` to split it into two provider-specific classes sharing a common base. This improves maintainability as Stripe and PayPal have different CSS selectors and payment flows.

## Problem
The current `SaleViewTestLive` class handles both PayPal and Stripe tests using conditional logic and duplicate test names (which can lead to tests being skipped or overwritten). The CSS selectors and payment flows are significantly different between the two providers, making the single class bloated and hard to maintain.

## Solution
1. Introduce a `SaleViewLiveBase` class that contains:
    - Common `setUp` and `tearDown`.
    - Shared helper methods like `__load_checkout_page__`, `__click__`, and `__send_text__`.
    - Generic test templates for common scenarios (e.g., checking total, promo codes).
2. Create `SaleViewPaypalLiveTest` inheriting from `SaleViewLiveBase`:
    - Use `@override_settings(PAYMENT_PROVIDER="paypal")`.
    - Define PayPal-specific selectors.
    - Implement the PayPal sandbox payment flow.
3. Create `SaleViewStripeLiveTest` inheriting from `SaleViewLiveBase`:
    - Use `@override_settings(PAYMENT_PROVIDER="stripe")`.
    - Define Stripe-specific selectors.
    - Implement the Stripe sandbox payment flow (card details and submission).

## Benefits
- **Cleanliness**: Each provider's test class only contains logic relevant to that provider.
- **Maintainability**: Changes in one provider's checkout flow won't affect the other's tests.
- **Reliability**: Fixes the issue of duplicate test names and ensures both providers are tested thoroughly.
