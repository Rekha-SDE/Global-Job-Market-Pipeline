document.querySelectorAll('[data-password-toggle]').forEach((button) => {
  button.addEventListener('click', () => {
    const input = button.parentElement.querySelector('input');
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'Hide' : 'Show';
    button.setAttribute('aria-label', `${show ? 'Hide' : 'Show'} password`);
  });
});

document.querySelectorAll('[data-auth-form]').forEach((form) => {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = form.querySelector('.form-message');
    const isRegistration = Boolean(form.querySelector('[name="terms"]'));
    if (!form.checkValidity()) {
      message.textContent = 'Please check the fields above and try again.';
      message.hidden = false;
      form.reportValidity();
      return;
    }

    const values = Object.fromEntries(new FormData(form).entries());
    const payload = isRegistration
      ? {name: values.name.trim(), email: values.email.trim(), password: values.password}
      : {email: values.email.trim(), password: values.password};
    const button = form.querySelector('[type="submit"]');
    button.disabled = true;
    message.hidden = true;
    try {
      const response = await fetch(`http://127.0.0.1:8000/auth/${isRegistration ? 'register' : 'login'}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'We could not complete your request.');
      sessionStorage.setItem('careerMapToken', result.access_token);
      sessionStorage.setItem('careerMapUser', JSON.stringify(result.user));
      window.location.assign('index.html');
    } catch (error) {
      message.textContent = error instanceof TypeError
        ? 'Could not reach the account service. Start the API and open this page through Live Server (port 5500).'
        : error.message;
      message.hidden = false;
    } finally {
      button.disabled = false;
    }
  });
});

document.querySelectorAll('[data-demo-link]').forEach((link) => {
  link.addEventListener('click', (event) => event.preventDefault());
});
