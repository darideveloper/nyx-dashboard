// Main components
const formSignUp = document.querySelector('#form-sign-up')

// Sign up form custom validation
function signUp() {
  const form = formSignUp

  const errorPass = document.querySelector('.error-pass')
  const errorPassContent = errorPass.querySelector('p')
  const passRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@$.#\?!%*&^*_\\-])[A-Za-z0-9@$.#\?!%*&^*_\\-]{8,50}$/



  form.addEventListener('submit', (e) => {
    e.preventDefault()
    const password1 = form.querySelector('input[name="password1"]').value
    const password2 = form.querySelector('input[name="password2"]').value

    if (!passRegex.test(password1)) {
      // Validate password strength
      errorPass.classList.remove('hidden')
      errorPassContent.textContent = 'Password must be 8-50 characters long and contain at least one lowercase letter, one uppercase letter, one number, and one special character'
    } else if (password1 !== password2) {
      // Validate password match
      errorPass.classList.remove('hidden')
      errorPassContent.textContent = 'Passwords do not match'
    } else {
      // Hide error message
      errorPass.classList.add('hidden')

      // Submit form if all validations pass
      form.submit()
    } 

    console.log({password1, password2})
  })
}


// Run main components custom functions
if (formSignUp) {
  signUp()
}