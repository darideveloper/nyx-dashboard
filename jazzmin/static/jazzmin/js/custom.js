// Main components
const formSignUp = document.querySelector('#form-sign-up')
const formResetPass = document.querySelector('#form-reset-pass')
const errorElem = document.querySelector('.callout.callout-danger')
const adminH1 = document.querySelector('h1').textContent.toLowerCase().trim()

// Base class for error messages in forms
class ErrorMessages {
  showError(text) {

    // Clean old error
    errorElem.innerHTML = ""

    // Add new error
    errorElem.classList.remove('hidden')
    const errorPassContent = document.createElement('p')
    errorPassContent.textContent = text
    errorElem.appendChild(errorPassContent)
  }

  invalidInput(elem) {
    elem.parentNode.classList.add('is-invalid')
    elem.focus()
  }

  resetInvalidInput(elem) {
    elem.parentNode.classList.remove('is-invalid')
  }
}

class ValdiatePass extends ErrorMessages {

  constructor(pass1Selector, pass2Selector) {

    super()

    // Get elements and values
    this.password1Elem = document.querySelector(pass1Selector)
    this.password2Elem = document.querySelector(pass2Selector)

    this.isValid = false

    // Regex
    this.passRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])[A-Za-z0-9\W_]{8,50}$/
  }

  validate() {

    const password1 = this.password1Elem.value
    const password2 = this.password2Elem.value

    // Reset inputs
    this.resetInvalidInput(this.password1Elem)
    this.resetInvalidInput(this.password2Elem)

    // Validate password strength
    if (!this.passRegex.test(password1)) {
      this.showError('Password must be 8-50 characters long and contain at least one lowercase letter, one uppercase letter and one number')
      this.invalidInput(this.password1Elem)

      // Validate password match
    } else if (password1 !== password2) {
      this.showError('Passwords do not match')
      this.invalidInput(this.password2Elem)
      this.invalidInput(this.password1Elem)

      // Update validation status
    } else {
      this.isValid = true
    }
  }
}

// Sign up form custom validation
class SignUp extends ErrorMessages {

  constructor() {

    super()

    // Elements
    this.form = formSignUp
    this.emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/

    // Passowrd validation
    this.passwordValdiator = new ValdiatePass(
      'input[name="password1"]',
      'input[name="password2"]'
    )

    // Custom submit event
    this.form.addEventListener('submit', (e) => {
      e.preventDefault()
      this.onSubmit()
    })
  }

  onSubmit(e) {

    const emailElem = this.form.querySelector('input[name="email"]')
    const email = emailElem.value

    // Remove old errors
    this.resetInvalidInput(emailElem)

    // Validate email
    if (!this.emailRegex.test(email)) {
      this.showError('Invalid email address')
      this.invalidInput(emailElem)
    } else {

      // Validate password
      this.passwordValdiator.validate()
      const isPassValid = this.passwordValdiator.isValid

      // Submit form if all validations pass
      if (isPassValid) {
        // Hide error message
        errorElem.classList.add('hidden')

        // Submit form if all validations pass
        this.form.submit()
      }
    }
  }
}

// Reset pass form custom validation
class ResetPass extends ValdiatePass {

  constructor() {

    // Initialize parent class
    const pass1Selector = 'input[name="new-password-1"]'
    const pass2Selector = 'input[name="new-password-2"]'
    super(pass1Selector, pass2Selector)

    this.form = formResetPass

    // Custom submit event
    this.form.addEventListener('submit', (e) => {
      e.preventDefault()
      this.onSubmit()
    })
  }

  onSubmit(e) {

    this.validate()
    if (this.isValid) {
      // Hide error message
      errorElem.classList.add('hidden')

      // Submit form if all validations pass
      this.form.submit()
    }
  }
}

// Countdown component in index page
class Countdown {

  constructor() {

    // Elements
    this.daysElement = document.getElementById('days')
    this.hoursElement = document.getElementById('hours')
    this.minutesElement = document.getElementById('minutes')
    this.secondsElement = document.getElementById('seconds')
    this.statusElement = document.getElementById('status')

    this.buttonNotify = document.querySelector('#actionButtonNotify')
    this.buttonBuy = document.querySelector('#actionButtonBuy')
    this.buttonUnsubscribe = document.querySelector('#actionButtonUnsubscribe')

    // Control variables
    this.totalSeconds = 0
    this.alreadySubscribed = false
    this.actionType = 'add'


    // Run main functions
    this.setupButtonEvents()
    this.loadSeconds().then(() => {

      // Update counter values
      this.setupCounter()

      // Update buttons
      if (this.alreadySubscribed) {
        this.toggleButtons()
      }
    })
  }

  toggleButtons() {
    // Toggle ubsubscribe and notify me buttons
    this.buttonNotify.classList.toggle("hidden")
    this.buttonUnsubscribe.classList.toggle("hidden")
  }

  async loadSeconds() {
    // set in class next future strock from api
    const response = await fetch(`/api/store/next-future-stock/${userEmail}`)
    const data = await response.json()
    this.totalSeconds = data.next_future_stock
    this.alreadySubscribed = data.already_subscribed
  }

  updateCounter() {
    const days = Math.floor(this.totalSeconds / (3600 * 24))
    const hours = Math.floor(this.totalSeconds % (3600 * 24) / 3600)
    const minutes = Math.floor(this.totalSeconds % 3600 / 60)
    const seconds = Math.floor(this.totalSeconds % 60)

    this.daysElement.textContent = days.toString().padStart(2, '0')
    this.hoursElement.textContent = hours.toString().padStart(2, '0')
    this.minutesElement.textContent = minutes.toString().padStart(2, '0')
    this.secondsElement.textContent = seconds.toString().padStart(2, '0')
  }

  endCountdown() {
    // Update text 
    this.statusElement.textContent = 'New sets are available now!'

    // Disable notify me button and enabe buy button
    this.buttonNotify.classList.add("hidden")
    this.buttonBuy.classList.remove("hidden")
  }

  setupCounter() {

    if (this.totalSeconds <= 0) {
      this.endCountdown()
    } else {
      const interval = setInterval(() => {
        if (this.totalSeconds > 0) {
          this.totalSeconds -= 1
          this.updateCounter()

          if (this.totalSeconds <= 0) {
            clearInterval(interval)
            this.endCountdown()
          }
        }
      }, 1000)
    }
  }

  setupButtonEvents() {
    // Send json when click notify me button
    this.buttonNotify.addEventListener("click", (e) => {
      const email = e.target.getAttribute('data-email')

      // Send json post
      const jsonData = {
        "email": email,
        "type": "add",
      }
      const endpoint = `/api/store/future-stock-subscription/`
      fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jsonData)
      })
        .then(response => response.json())
        .then(data => {
          this.toggleButtons()

          Swal.fire({
            icon: 'success',
            title: 'Subscription successful',
            text: 'You will be notified by email when new sets are available',
          })
        })
    })

    this.buttonUnsubscribe.addEventListener("click", (e) => {
      const email = e.target.getAttribute('data-email')

      // Send json post
      const jsonData = {
        "email": email,
        "type": "remove",
      }
      const endpoint = `/api/store/future-stock-subscription/`
      fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jsonData)
      })
        .then(response => response.json())
        .then(data => {
          this.toggleButtons()

          Swal.fire({
            icon: 'success',
            title: 'Unsubscription successful',
            text: 'You will no longer receive notifications by email',
          })
        })
    })
  }
}


class AdminSale {

  constructor() {

    const currentUrl = window.location.href
    if (currentUrl.includes('change')) {
      // Edit view buyer customization
      this.removeLinksHref()
    } else {
      // List view buyer customization
      this.hideFilters()
      this.hideUserColumn()
    }

  }

  // Hide some filter to no-admin users
  hideFilters() {
    if (!isAdmin) {

      const filtersSelectors = [
        'select[data-name="user"]',
        'select[data-name="country"]',
        'select[data-name="state"]',
        'select[data-name="promo_code"]',
      ]

      const filtersSelector = filtersSelectors.join(', ')
      const filters = document.querySelectorAll(filtersSelector)
      filters.forEach(filter => {
        const parentFilter = filter.parentNode
        parentFilter.remove()
      })
    }
  }

  // Hide user column in list view
  hideUserColumn() {
    if (!isAdmin) {
      const userCellsSelector = "th:nth-child(2), td:nth-child(2)"
      const userCells = document.querySelectorAll(userCellsSelector)
      console.log({ userCells })
      userCells.forEach(cell => {
        cell.remove()
      })
    }
  }

  // Remove href from links in change view
  removeLinksHref() {

    if (!isAdmin) {
      const linkSelector = '.card-body a'
      const links = document.querySelectorAll(linkSelector)
      links.forEach(link => {
        link.removeAttribute('href')
      })
    }

  }

}


// Run main components custom functions
if (formSignUp) {
  // Validate sign up form
  new SignUp()
} else if (formResetPass) {
  // Validate reset pass form
  new ResetPass()
} else if (adminH1 == 'dashboard') {
  // Start countdown component
  new Countdown()
} else if (adminH1 == 'orders') {
  // Start admin sales component
  new AdminSale()
}

// Global styles
const menuItems = document.querySelectorAll('.d-sm-inline-block a.nav-link')
menuItems.forEach(item => {
  item.classList.add('btn')
  item.classList.add('btn-primary')
  item.classList.add('text-light')
})
