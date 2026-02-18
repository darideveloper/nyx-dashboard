# Tasks: Add Stripe Integration Tests

## Preparation
- [x] Add `INVOICE_STRIPE_COMMISSION` to `nyx_dashboard/settings.py` (matching PayPal pattern).
- [x] Ensure `STRIPE_API_KEY` (test key) is in `.env.testing`.

## Refactoring Base Logic
- [x] Create `store/tests/payment_base.py`:
    - Move `SaleViewTest` methods to `SaleViewTestMixin`.
    - Add abstract properties/methods:
        - `provider_name` (str)
        - `payment_link_domain` (str)
        - `assert_payment_link(url)`
- [x] Update `SaleViewTest`:
    - Rename to `SaleViewPaypalTest`.
    - Inherit from `SaleViewTestMixin` and `TestCase`.
    - Set `PAYMENT_PROVIDER='paypal'`.
- [x] Ensure `SaleDoneViewTest` checks specific provider invoice details:
    - [x] Create `SaleDoneViewTestMixin` in `store/tests/payment_base.py`.
    - [x] Refactor `SaleDoneViewTest` into `SaleDonePaypalTest` (inheriting from Mixin).
    - [x] Implement `SaleDoneStripeTest` with `commission_rate` property and necessary mocking.
    - [x] Validate `igi` and `provider_fee` calculations match settings in `test_invoice_content`.

## Stripe Unit Tests
- [x] Create `store/tests/test_stripe_integration.py`:
    - [x] Test `StripeCheckout.get_checkout_link`.
    - [x] Test `StripeCheckout.is_payment_done` (Mocked).
- [x] Update `SaleDoneViewTest`:
    - [x] Add `test_stripe_invoice_content`: Executes the same logic as `test_invoice_content` but for Stripe.

## Stripe Live Tests (Selenium)
- [x] Update `SaleViewTestLive`:
    - [x] Create `store/tests/pages/stripe_checkout_page.py` (Page Object):
        - `fill_card_details(number, expiry, cvc, zip)`
        - `submit_payment()`
    - [x] Parameterize `test_pay_sandbox_user`:
        - Add logic to branch based on `settings.PAYMENT_PROVIDER` or subclass.
    - [x] Implement `test_pay_stripe_sandbox_user`:
        - Override settings: `@override_settings(PAYMENT_PROVIDER='stripe')`.
        - Verify Stripe checkout page loads (check URL/title).
        - Fill valid test card (4242 4242 4242 4242).
        - Assert redirect URL contains `sale-status=success`.

## Verification
- [x] Run `python manage.py test store.tests.test_views`.
- [x] Verify both PayPal and Stripe tests pass sequentially.
- [x] Perform manual verification with `PAYMENT_PROVIDER=stripe`.
