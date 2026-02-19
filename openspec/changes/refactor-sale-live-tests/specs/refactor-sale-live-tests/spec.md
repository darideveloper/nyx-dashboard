# Capability: Refactor Sale Live Tests

Refactor E2E tests for the sale view to use a provider-specific class hierarchy.

## MODIFIED Requirements

### Requirement: Provider-Specific E2E Tests
The E2E tests for the sale checkout process MUST be isolated by payment provider to handle differences in UI selectors and payment flows.

#### Scenario: PayPal E2E Checkout
- **Given** the payment provider is set to "paypal".
- **When** a user initiates a sale and proceeds to the PayPal checkout page.
- **Then** the test must use PayPal-specific CSS selectors to validate the total amount and complete the sandbox payment process.

#### Scenario: Stripe E2E Checkout
- **Given** the payment provider is set to "stripe".
- **When** a user initiates a sale and proceeds to the Stripe checkout page.
- **Then** the test must use Stripe-specific CSS selectors and the Stripe-specific payment flow (card entry and submission) to validate and complete the payment.
