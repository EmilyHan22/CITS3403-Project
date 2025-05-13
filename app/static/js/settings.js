// static/js/settings.js
document.addEventListener('DOMContentLoaded', () => {
    // --- Password-strength logic ---
    const pw       = document.getElementById('new_password');
    const reqs = {
      length:    document.getElementById('req-length'),
      uppercase: document.getElementById('req-upper'),
      lowercase: document.getElementById('req-lower'),
      number:    document.getElementById('req-number'),
      special:   document.getElementById('req-special')
    };
  
    function markValid(el) {
      el.classList.add('text-success');
      const icon = el.querySelector('i');
      icon.classList.remove('fa-times');
      icon.classList.add('fa-check');
    }
    function markInvalid(el) {
      el.classList.remove('text-success');
      const icon = el.querySelector('i');
      icon.classList.remove('fa-check');
      icon.classList.add('fa-times');
    }
  
    if (pw) {
      pw.addEventListener('input', () => {
        const v = pw.value;
        v.length >= 8       ? markValid(reqs.length)    : markInvalid(reqs.length);
        /[A-Z]/.test(v)      ? markValid(reqs.uppercase) : markInvalid(reqs.uppercase);
        /[a-z]/.test(v)      ? markValid(reqs.lowercase) : markInvalid(reqs.lowercase);
        /\d/.test(v)         ? markValid(reqs.number)    : markInvalid(reqs.number);
        /[!@#$%^&*(),.?":{}|<>]/.test(v)
                             ? markValid(reqs.special)   : markInvalid(reqs.special);
      });
    }
  
    // --- Delete-account logic ---
    const delBtn     = document.getElementById('delete-account-btn');
    const form       = document.getElementById('delete-account-form');
    const input      = document.getElementById('delete-confirm-input');
    const confirmBtn = document.getElementById('delete-confirm-btn');
  
    delBtn.addEventListener('click', () => {
      form.style.display = 'block';
      input.focus();
    });
    input.addEventListener('input', () => {
      if (input.value === 'DELETE') {
        confirmBtn.removeAttribute('disabled');
      } else {
        confirmBtn.setAttribute('disabled', 'disabled');
      }
    });
  });
  