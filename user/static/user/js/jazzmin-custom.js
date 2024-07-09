// Main components
const formSignUp = document.querySelector('#form-sign-up')

// Sign up form custom validation
class SignUp {

  constructor() {
    
    // Elements
    this.form = formSignUp
    this.errorElem = document.querySelector('.callout.callout-danger')
    this.passRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@$.#\?!%*&^*_\\-])[A-Za-z0-9@$.#\?!%*&^*_\\-]{8,50}$/
    this.emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/

    // Submit event
    this.form.addEventListener('submit', (e) => {
      e.preventDefault()
      this.onSubmit()
    })

  }
  
  showError(text) {

    // Clean old error
    this.errorElem.innerHTML = ""

    // Add new error
    this.errorElem.classList.remove('hidden')
    const errorPassContent = document.createElement('p')
    errorPassContent.textContent = text
    this.errorElem.appendChild(errorPassContent)
  }

  invalidInput(elem) {
    elem.parentNode.classList.add('is-invalid')
    elem.focus()
  }

  resetInvalidInput(elem) {
    elem.parentNode.classList.remove ('is-invalid')
  }

  onSubmit(e) {

    // Get elements and values
    const password1Elem = this.form.querySelector('input[name="password1"]')
    const password2Elem  = this.form.querySelector('input[name="password2"]')
    const emailElem = this.form.querySelector('input[name="email"]')

    const password1 = password1Elem.value
    const password2 = password2Elem.value
    const email = emailElem.value

    // Remove old errors
    this.resetInvalidInput(password1Elem)
    this.resetInvalidInput(password2Elem)
    this.resetInvalidInput(emailElem)
    
    if (!this.emailRegex.test(email)) {      
      // Validate email
      this.showError('Invalid email address')
      this.invalidInput(emailElem)
    } else if (!this.passRegex.test(password1)) {
      // Validate password strength
      this.showError('Password must be 8-50 characters long and contain at least one lowercase letter, one uppercase letter, one number, and one special character')
      this.invalidInput(password1Elem)
    } else if (password1 !== password2) {
      // Validate password match
      this.showError('Passwords do not match')
      this.invalidInput(password2Elem)
      this.invalidInput(password1Elem)
    } else {
      // Hide error message
      this.errorElem.classList.add('hidden')
  
      // Submit form if all validations pass
      this.form.submit()
    }
  }

}


// Run main components custom functions
if (formSignUp) {
  new SignUp()
}