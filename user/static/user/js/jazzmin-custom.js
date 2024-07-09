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

  onSubmit(e) {

    const password1 = this.form.querySelector('input[name="password1"]').value
    const password2 = this.form.querySelector('input[name="password2"]').value
    const email = this.form.querySelector('input[name="email"]').value
    
    if (!this.emailRegex.test(email)) {      
      // Validate email
      this.showError('Invalid email address')
    } else if (!this.passRegex.test(password1)) {
      // Validate password strength
      this.showError('Password must be 8-50 characters long and contain at least one lowercase letter, one uppercase letter, one number, and one special character')
    } else if (password1 !== password2) {
      // Validate password match
      this.showError('Passwords do not match')
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