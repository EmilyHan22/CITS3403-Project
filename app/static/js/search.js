document.addEventListener('DOMContentLoaded', () => {
    const input       = document.getElementById('searchInput');
    const suggestions = document.getElementById('searchSuggestions');
    let timer;
  
    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) {
        suggestions.style.display = 'none';
        return;
      }
  
      timer = setTimeout(() => {
        fetch(`/search_users?q=${encodeURIComponent(q)}`)
          .then(r => r.json())
          .then(list => {
            console.log("🔍 search_users returned:", list);
            suggestions.innerHTML = '';
            if (!list.length) {
              suggestions.innerHTML = '<button class="list-group-item">No matches</button>';
            } else {
                list.forEach(u => {
                    // u might be a string ("alice") or an object ({ username, display_name })
                    const username = typeof u === 'string' ? u : u.username;
                    const label    = typeof u === 'string'
                                     ? u
                                     : (u.display_name || u.username);
                  
                    const btn = document.createElement('button');
                    btn.type           = 'button';
                    btn.className      = 'list-group-item list-group-item-action';
                    btn.textContent    = label;
                    btn.addEventListener('click', () => {
                      window.location.href = `/profile/${username}`;
                    });
                    suggestions.append(btn);
                  });
            }
            suggestions.style.display = 'block';
          })
          .catch(console.error);
      }, 300);
    });
  
    // hide on outside click
    document.addEventListener('click', e => {
      if (!input.contains(e.target) && !suggestions.contains(e.target)) {
        suggestions.style.display = 'none';
      }
    });
  });
  