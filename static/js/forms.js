document.addEventListener('DOMContentLoaded', function() {
    // Form validation and submission handling
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.hasAttribute('data-no-ajax')) {
                e.preventDefault();
                submitForm(form);
            }
        });
    });

    // Date input handling
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        // Set max date to today
        input.max = new Date().toISOString().split('T')[0];

        // Validate date on change
        input.addEventListener('change', function() {
            validateDate(input);
        });
    });

    // Number input handling
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            validateNumber(input);
        });
    });
});

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function submitForm(form) {
    const formData = new FormData(form);
    const url = form.action;
    const submitButton = form.querySelector('button[type="submit"]');

    // Disable submit button during submission
    if (submitButton) submitButton.disabled = true;

    // Clear previous errors
    clearFormErrors(form);

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert('success', gettext('Data saved successfully!'));
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                form.reset();
            }
        } else {
            showAlert('danger', data.message || gettext('Error saving data.'));
            if (data.errors) {
                showFormErrors(form, data.errors);
            }
        }
    })
    .catch(error => {
        showAlert('danger', gettext('An error occurred. Please try again.'));
        console.error('Error:', error);
    })
    .finally(() => {
        if (submitButton) submitButton.disabled = false;
    });
}

function validateDate(input) {
    const date = new Date(input.value);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (date > today) {
        input.setCustomValidity(gettext('Date cannot be in the future'));
        showFieldError(input, gettext('Date cannot be in the future'));
    } else {
        input.setCustomValidity('');
        clearFieldError(input);
    }
}

function validateNumber(input) {
    const value = parseFloat(input.value);
    const min = parseFloat(input.min);
    const max = parseFloat(input.max);

    if (isNaN(value)) {
        input.setCustomValidity(gettext('Please enter a valid number'));
        showFieldError(input, gettext('Please enter a valid number'));
    } else if (min !== undefined && value < min) {
        input.setCustomValidity(gettext('Value must be greater than or equal to ') + min);
        showFieldError(input, gettext('Value must be greater than or equal to ') + min);
    } else if (max !== undefined && value > max) {
        input.setCustomValidity(gettext('Value must be less than or equal to ') + max);
        showFieldError(input, gettext('Value must be less than or equal to ') + max);
    } else {
        input.setCustomValidity('');
        clearFieldError(input);
    }
}

function showFormErrors(form, errors) {
    Object.keys(errors).forEach(field => {
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            showFieldError(input, errors[field]);
        }
    });
}

function clearFormErrors(form) {
    form.querySelectorAll('.is-invalid').forEach(input => {
        clearFieldError(input);
    });
}

function showFieldError(input, message) {
    clearFieldError(input);
    input.classList.add('is-invalid');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    input.parentNode.appendChild(errorDiv);
}

function clearFieldError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const alertsContainer = document.getElementById('alerts-container');
    if (alertsContainer) {
        alertsContainer.appendChild(alertDiv);
    } else {
        // Create alerts container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'alerts-container';
        container.className = 'container mt-3';
        container.appendChild(alertDiv);
        document.querySelector('main').prepend(container);
    }

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}