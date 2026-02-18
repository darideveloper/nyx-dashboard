# Capability: Stripe Test Coverage

## Added Requirements

### Requirement: Verified Stripe Checkout
The system MUST provide automated verification that Stripe checkout sessions are correctly initialized and resolved.

#### Scenario: Stripe Link Generation
- **Given** a new `Sale` is created with `PAYMENT_PROVIDER` set to "stripe".
- **When** the `Sale` view is called.
- **Then** the response must contain a `payment_link` starting with `https://checkout.stripe.com/`.

#### Scenario: Stripe Payment Confirmation
- **Given** a `Sale` with a valid Stripe `payment_link`.
- **When** `SaleDoneView` is accessed with `use_testing=true`.
- **Then** the `Sale` status must be updated to "Paid".
- **And** an invoice must be generated using `INVOICE_STRIPE_COMMISSION`.

### Requirement: Live Payment Handshake (Stripe)
The system MUST support end-to-end integration tests for Stripe using Selenium.

#### Scenario: Stripe Sandbox Payment
- **Given** a browser is on the Stripe Checkout page.
- **When** the standard Stripe test card (4242...) and valid test data are submitted.
- **Then** the browser must redirect back to the `nyx-dashboard` success page.
- **And** the `Sale` status must be "Paid".
