# Tasks: Refactor Sale Live Tests

- [ ] Create `SaleViewLiveBase` class in `store/tests/test_views.py`
    - Move common `setUp`, `tearDown`, and helpers from `SaleViewTestLive`.
    - Implement `test_checkout_total` and `test_checkout_promo_code` as generic methods.
- [ ] Implement `SaleViewPaypalLiveTest(SaleViewLiveBase)`
    - Set `@override_settings(PAYMENT_PROVIDER="paypal")`.
    - Define PayPal selectors in `setUp`.
    - Move and adapt `test_pay_sandbox_user_paypal`.
- [ ] Implement `SaleViewStripeLiveTest(SaleViewLiveBase)`
    - Set `@override_settings(PAYMENT_PROVIDER="stripe")`.
    - Define Stripe selectors in `setUp` (requires investigation/updating).
    - Move Stripe-specific helpers (`__fill_stripe_card_details__`, `__submit_stripe_payment__`).
    - Move and adapt `test_pay_stripe_sandbox_user`.
- [ ] Remove legacy `SaleViewTestLive` class.
- [ ] Validate tests pass for both providers.
    - Run `python manage.py test store.tests.test_views.SaleViewPaypalLiveTest`
    - Run `python manage.py test store.tests.test_views.SaleViewStripeLiveTest`
