
// Remove filters for non-admin users
addEventListener('DOMContentLoaded', function () {
  const filtersForm = document.querySelector('#changelist-search')
  if (filtersForm && !isAdmin) {
    filtersForm.remove()
  }
})