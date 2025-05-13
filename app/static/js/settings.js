document.addEventListener('DOMContentLoaded', () => {
    // — Profile‐pic live preview —
    const fileInput = document.getElementById('profile_pic');
    const preview   = document.getElementById('settingsAvatarPreview');
    fileInput?.addEventListener('change', () => {
      const file = fileInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => preview.src = reader.result;
      reader.readAsDataURL(file);
    });
  
    // — Delete‐account confirmation toggle —
    const delBtn   = document.getElementById('delete-account-btn');
    const delForm  = document.getElementById('delete-account-form');
    const delInput = document.getElementById('delete-confirm-input');
    const delOK    = document.getElementById('delete-confirm-btn');
  
    delBtn?.addEventListener('click', () => {
      delForm.style.display = 'block';
      delBtn.style.display  = 'none';
    });
    delInput?.addEventListener('input', () => {
      delOK.disabled = delInput.value !== 'DELETE';
    });
  
    // — Password‐strength checker —
    const pwInput = document.getElementById('new_password');
    const reqBox  = document.querySelector('.pw-req-box');
    const checks  = {
      length:  { regex: /.{8,}/,                    id: 'req-length'  },
      upper:   { regex: /[A-Z]/,                    id: 'req-upper'   },
      lower:   { regex: /[a-z]/,                    id: 'req-lower'   },
      number:  { regex: /\d/,                       id: 'req-number'  },
      special: { regex: /[!@#$%^&*(),.?":{}|<>]/,    id: 'req-special' },
    };
  
    // show popover when focusing the input
    pwInput?.addEventListener('focus', () => {
      reqBox.classList.add('show');
    });
  
    // hide popover when blurring the input
    pwInput?.addEventListener('blur', () => {
      reqBox.classList.remove('show');
    });
  
    // update each requirement on input
    pwInput?.addEventListener('input', () => {
      const val = pwInput.value;
      Object.values(checks).forEach(({ regex, id }) => {
        const li   = document.getElementById(id);
        const icon = li.querySelector('i');
        if (regex.test(val)) {
          icon.classList.replace('fa-times', 'fa-check');
        } else {
          icon.classList.replace('fa-check', 'fa-times');
        }
      });
    });
  });
  