## ADDED Requirements

### Requirement: Fill Stripe Card Details
The system MUST provide a method `__fill_stripe_card_details__` that populates the Stripe checkout form with card information.

#### Scenario: Fill Stripe Card Details
Given I am on the Stripe Checkout page
When I call `__fill_stripe_card_details__` with valid card information
Then the Card Number, Expiry, and CVC fields should be populated correctly
And the Zip Code field should be populated if present

### Requirement: Submit Stripe Payment
The system MUST provide a method `__submit_stripe_payment__` that clicks the submission button on the Stripe checkout page.

#### Scenario: Submit Stripe Payment
Given I have filled in valid card details on the Stripe Checkout page
When I call `__submit_stripe_payment__`
Then the "Pay" button should be clicked
And the payment process should initiate
