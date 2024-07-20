// Main components
const formSignUp = document.querySelector('#form-sign-up')
const formResetPass = document.querySelector('#form-reset-pass')
const errorElem = document.querySelector('.callout.callout-danger')
const adminH1 = document.querySelector('h1').textContent.toLowerCase().trim()

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

function setupCounter() {

  // Count down timer
  let totalSeconds = 0
  let totalSecondsLoaded = false
  const nextFutureStock = 10 // Replace this with your actual value

  // Get next future strock from api
  fetch('/api/store/next-future-stock')
    .then(response => response.json())
    .then(data => {
      totalSeconds = data.next_future_stock
      console.log({ totalSeconds })
      totalSecondsLoaded = true
    })

  const daysElement = document.getElementById('days')
  const hoursElement = document.getElementById('hours')
  const minutesElement = document.getElementById('minutes')
  const secondsElement = document.getElementById('seconds')
  const statusElement = document.getElementById('status')

  function updateCounter() {
    const days = Math.floor(totalSeconds / (3600 * 24))
    const hours = Math.floor(totalSeconds % (3600 * 24) / 3600)
    const minutes = Math.floor(totalSeconds % 3600 / 60)
    const seconds = Math.floor(totalSeconds % 60)

    daysElement.textContent = days.toString().padStart(2, '0')
    hoursElement.textContent = hours.toString().padStart(2, '0')
    minutesElement.textContent = minutes.toString().padStart(2, '0')
    secondsElement.textContent = seconds.toString().padStart(2, '0')
  }

  if (!totalSecondsLoaded && nextFutureStock !== 0) {
    totalSeconds = nextFutureStock
    totalSecondsLoaded = true
  }

  if (totalSecondsLoaded) {
    const interval = setInterval(() => {
      if (totalSeconds > 0) {
        totalSeconds -= 1
        updateCounter()

        if (totalSeconds <= 0) {
          clearInterval(interval)
          statusElement.textContent = 'New sets are available now!'
        }
      }
    }, 1000)
  }
}

// Run main components custom functions
if (formSignUp) {
  new SignUp()
} else if (formResetPass) {
  new ResetPass()
} else if (adminH1 == 'dashboard') {
  setupCounter()
}

console.log({adminH1})