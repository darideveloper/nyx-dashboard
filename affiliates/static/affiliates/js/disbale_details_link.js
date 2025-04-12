// Remove details links for no active users
addEventListener('DOMContentLoaded', function() {
  if (!isAdmin) {
    const links = document.querySelectorAll('tbody a');
    links.forEach(link => {
      // Change tag to p
      link.removeAttribute('href');
    })
  }
});
