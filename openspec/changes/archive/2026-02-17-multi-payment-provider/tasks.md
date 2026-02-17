# Payment Provider Implementation Tasks

## Preparation
- [x] Create `openspec/changes/multi-payment-provider` directory and files (Done).
- [x] Verify `stripe` library version in `requirements.txt`.

## Utils Implementation
- [x] Create `utils/payment_provider.py` (optional, or just logic in views) or rewrite `utils/stripe.py` to contain the `StripeCheckout` class.
    - [x] Implement `get_checkout_link`.
    - [x] Implement `is_payment_done`.
- [x] Validate `utils/paypal.py` for interface consistency (duck typing).

## Views Update
- [x] Modify `store/views.py`:
    - [x] Import `StripeCheckout`.
    - [x] Implement `get_payment_provider()` helper function in `store/views.py` (or external util).
    - [x] Update `Sale.post` to use `get_payment_provider()`.
    - [x] Update `SaleDone.get` to use `get_payment_provider(sale=sale)`.
    - [x] Update `PaymentLink.get` to use `get_payment_provider(sale=sale)`.

## Settings
- [x] Add `PAYMENT_PROVIDER` to `nyx_dashboard/settings.py` (default: "paypal").
- [x] Ensure `STRIPE_SECRET_KEY` is loaded.

## Verification
- [x] Validate `openspec validate multi-payment-provider --strict`.
- [x] Manual test: Verify PayPal checkout still works (regression test).
- [x] Manual test: Enable Stripe via env var and verify checkout flow.
