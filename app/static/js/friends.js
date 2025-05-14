document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('friendSearch');
    const suggestions = document.getElementById('searchSuggestions');
    const sendBtn     = document.getElementById('sendRequestBtn');
  
    // Typeahead
    let timer;
    searchInput.addEventListener('input', () => {
      clearTimeout(timer);
      const q = searchInput.value.trim();
      if (q.length < 2) return suggestions.style.display = 'none';
      timer = setTimeout(() => {
        fetch(`/search_users?q=${encodeURIComponent(q)}`)
          .then(r => r.json())
          .then(list => {
            suggestions.innerHTML = '';
            if (!list.length) {
              suggestions.innerHTML = '<button class="list-group-item">No matches</button>';
            } else {
              list.forEach(name => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'list-group-item list-group-item-action';
                btn.textContent = name;
                btn.addEventListener('click', () => {
                  searchInput.value = name;
                  suggestions.style.display = 'none';
                });
                suggestions.append(btn);
              });
            }
            suggestions.style.display = 'block';
          });
      }, 300);
    });
  
    // Send request
    sendBtn.addEventListener('click', () => {
      const username = searchInput.value.trim();
      if (!username) return;
      fetch('/send_friend_request', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({username})
      })
      .then(r => r.json())
      .then(j => {
        if (j.error) alert(j.error);
        else location.reload();
      });
    });
  
    // Accept / reject
    document.querySelectorAll('.accept-btn').forEach(btn =>
      btn.addEventListener('click', () => respond(btn.dataset.id, 'accept'))
    );
    document.querySelectorAll('.reject-btn').forEach(btn =>
      btn.addEventListener('click', () => respond(btn.dataset.id, 'reject'))
    );
    function respond(id, action) {
      fetch('/respond_friend_request',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({request_id: id, action})
      })
      .then(r=>r.json())
      .then(j=>{
        if (j.success) location.reload();
        else alert(j.error || 'Failed');
      });
    }
  
    // Remove friend
    document.querySelectorAll('.remove-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!confirm('Remove this friend?')) return;
        fetch(`/remove_friend/${btn.dataset.id}`, {method:'DELETE'})
          .then(r=>r.json())
          .then(j=>{
            if (j.success) location.reload();
            else alert(j.error || 'Failed');
          });
      });
    });
  });
  