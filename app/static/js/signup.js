document.addEventListener("DOMContentLoaded", () => {
    const pwInput = document.getElementById("password");
    const reqBox  = document.getElementById("password-requirements-box");
    if (!pwInput || !reqBox) return;
  
    const reqs = {
      length:    document.getElementById("length-req"),
      uppercase: document.getElementById("uppercase-req"),
      lowercase: document.getElementById("lowercase-req"),
      number:    document.getElementById("number-req"),
      special:   document.getElementById("special-req"),
    };
  
    // show popover
    pwInput.addEventListener("focus", () => reqBox.classList.add("show"));
    pwInput.addEventListener("blur",  () => reqBox.classList.remove("show"));
  
    // helper: turn on/off each line
    function toggle(el, ok) {
      const icon = el.querySelector("i");
      if (ok) {
        el.classList.add("text-success");
        el.classList.remove("text-danger");
        icon.classList.replace("fa-times", "fa-check");
      } else {
        el.classList.add("text-danger");
        el.classList.remove("text-success");
        icon.classList.replace("fa-check", "fa-times");
      }
    }
  
    // update on every keystroke
    pwInput.addEventListener("input", () => {
      const v = pwInput.value;
      toggle(reqs.length,    v.length >= 8);
      toggle(reqs.uppercase, /[A-Z]/.test(v));
      toggle(reqs.lowercase, /[a-z]/.test(v));
      toggle(reqs.number,    /\d/.test(v));
      toggle(reqs.special,   /[!@#$%^&*(),.?":{}|<>]/.test(v));
    });
  });
  