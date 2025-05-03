// Add friend
document.getElementById('addUserBtn').addEventListener('click', function() {
    const username = document.getElementById('userSearch').value.trim();
    if (!username) return;
    
    fetch('/add_friend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            // Add to following list
            const list = document.getElementById('followingList');
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                ${data.friend.username}
                <button class="btn btn-sm btn-outline-danger remove-friend" 
                        data-user-id="${data.friend.id}">
                    <i class="bi bi-trash"></i> Remove
                </button>
            `;
            list.appendChild(item);
            
            // Add event listener to new button
            item.querySelector('.remove-friend').addEventListener('click', removeFriend);
            
            // Clear search
            document.getElementById('userSearch').value = '';
        }
    });
});

// Remove friend
function removeFriend() {
    const listItem = this.closest('li');
    const friendId = this.dataset.userId;
    
    if (confirm(`Remove this user from your following?`)) {
        fetch(`/remove_friend/${friendId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                listItem.remove();
            }
        });
    }
}

// Add event listeners to existing buttons
document.querySelectorAll('.remove-friend').forEach(btn => {
    btn.addEventListener('click', removeFriend);
});