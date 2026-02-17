# Multi-Payment Provider

This proposal introduces a flexible payment provider system, allowing dynamic switching between PayPal and Stripe via environment variables.

## Motivation

The project currently supports only PayPal but has historical and broken Stripe code. Users require the ability to switch providers easily without code changes.

## High-Level Goal

Replace the static PayPal integration with a provider-agnostic interface that:
1.  Supports both PayPal and Stripe.
2.  Determines the active provider via `PAYMENT_PROVIDER` environment variable.
3.  Determines the processing provider for pending transactions based on the stored payment identifier format, ensuring backward compatibility and safe transitions.

## Affected Areas

*   **Payment Utilities**: `utils/paypal.py` (minor updates) and `utils/stripe.py` (rewrite).
*   **Store Views**: `store/views.py` (logic to use the active provider).
*   **Settings**: new `PAYMENT_PROVIDER` setting.
