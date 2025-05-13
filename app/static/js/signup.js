// static/js/signup.js
document.addEventListener('DOMContentLoaded', () => {
    const pw = document.getElementById('password');
    const reqs = {
      length:    document.getElementById('length-req'),
      uppercase: document.getElementById('uppercase-req'),
      lowercase: document.getElementById('lowercase-req'),
      number:    document.getElementById('number-req'),
      special:   document.getElementById('special-req')
    };
  
    function markValid(el) {
      el.classList.add('text-success');
      const icon = el.querySelector('i');
      icon.classList.remove('fa-times', 'text-muted');
      icon.classList.add('fa-check');
    }
  
    function markInvalid(el) {
      el.classList.remove('text-success');
      const icon = el.querySelector('i');
      icon.classList.remove('fa-check');
      icon.classList.add('fa-times', 'text-muted');
    }
  
    pw.addEventListener('input', () => {
      const v = pw.value;
      // length
      v.length >= 8       ? markValid(reqs.length)    : markInvalid(reqs.length);
      // uppercase
      /[A-Z]/.test(v)      ? markValid(reqs.uppercase) : markInvalid(reqs.uppercase);
      // lowercase
      /[a-z]/.test(v)      ? markValid(reqs.lowercase) : markInvalid(reqs.lowercase);
      // number
      /\d/.test(v)         ? markValid(reqs.number)    : markInvalid(reqs.number);
      // special char
      /[!@#$%^&*(),.?":{}|<>]/.test(v)
                            ? markValid(reqs.special)   : markInvalid(reqs.special);
    });
  });
  