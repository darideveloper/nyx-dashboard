# Implement Stripe E2E Checkout Tests

## Summary
Implement the helper methods in `SaleViewStripeTest` to enable comprehensive end-to-end testing of the Stripe checkout process using Selenium.

## Why
The current `SaleViewStripeTest` class has stubbed methods (`__fill_stripe_card_details__` and `__submit_stripe_payment__`) that rely on placeholders. This prevents automated validation of the full Stripe checkout flow, including card detail entry and payment submission.

## What Changes
Implement the methods using precise CSS selectors derived from the Stripe Hosted Checkout page structure.

### Implementation Details

#### CSS Selectors
Based on the provided Stripe Checkout HTML structure, the following selectors will be used:

- **Card Number**: `#cardNumber`
- **Expiry Date**: `#cardExpiry`
- **CVC**: `#cardCvc`
- **Zip Code**: `#billingPostalCode` (if present) or `input[name="billingPostalCode"]`
- **Submit Button**: `button[type="submit"]` or `[data-testid="hosted-payment-submit-button"]`

#### Code Changes
We will implement the methods in `SaleViewStripeTest`:

```python
    def __fill_stripe_card_details__(self, number, expiry, cvc, zip_code):
        \"\"\"Fill Stripe checkout card details\"\"\"

        # Ensure we are on the stripe page
        self.assertIn("checkout.stripe.com", self.driver.current_url)
        
        # Fill inputs
        self.__send_text__("#cardNumber", number)
        self.__send_text__("#cardExpiry", expiry)
        self.__send_text__("#cardCvc", cvc)
        
        # Zip code might be optional or auto-detected based on card/country
        try:
            # Check if zip code input is present and visible
            zip_input = self.driver.find_elements(By.CSS_SELECTOR, "#billingPostalCode")
            if zip_input and zip_input[0].is_displayed():
                zip_input[0].send_keys(zip_code)
        except Exception:
            # If zip code interaction fails, we log or ignore if not strictly required by test card
            pass

    def __submit_stripe_payment__(self):
        \"\"\"Submit Stripe payment\"\"\"
        # Click the pay button
        pay_button_selector = "button[type='submit']"
        # Or use the specific test id if stable
        # pay_button_selector = "[data-testid='hosted-payment-submit-button']"
        
        self.__click__(pay_button_selector)
```
