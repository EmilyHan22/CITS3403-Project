document.addEventListener('DOMContentLoaded', () => {
    const feedContainer = document.getElementById('feedContainer');
  
    // Delegate all clicks inside the feed container
    feedContainer.addEventListener('click', function(e) {
      const likeBtn    = e.target.closest('.like-btn');
      const commentBtn = e.target.closest('.comment-btn');
  
      if (likeBtn) {
        handleLike(likeBtn);
      }
      if (commentBtn) {
        handleComment(commentBtn);
      }
    });
  
    // Toggle like / unlike
    function handleLike(btn) {
      const card   = btn.closest('.card');
      const postId = card.dataset.postId;
      const liked  = btn.classList.contains('liked');
      const url    = `/api/posts/${postId}/like`;
      const method = liked ? 'DELETE' : 'POST';
  
      fetch(url, { method })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            btn.classList.toggle('liked');
            // swap icon: empty <3 vs filled <3
            btn.innerHTML = btn.classList.contains('liked')
              ? '<i class="bi bi-heart-fill text-danger"></i>'
              : '<i class="bi bi-heart"></i>';
            // update count next to it
            const countSpan = card.querySelector('.like-count');
            if (countSpan) countSpan.textContent = data.likes;
          } else {
            alert(data.error || 'Couldn’t update like');
          }
        })
        .catch(console.error);
    }
  
    // Show/hide comment box and post
    function handleComment(btn) {
      const card   = btn.closest('.card');
      let form     = card.querySelector('.comment-form');
  
      // toggle existing form
      if (form) {
        form.remove();
        return;
      }
  
      // build and insert comment form
      form = document.createElement('div');
      form.className = 'comment-form mt-2';
      form.innerHTML = `
        <input type="text" class="form-control mb-1 comment-input" placeholder="Write a comment…">
        <button class="btn btn-sm btn-primary submit-comment">Post</button>
      `;
      card.querySelector('.card-body').append(form);
  
      // attach submit handler
      form.querySelector('.submit-comment').addEventListener('click', () => {
        const postId = card.dataset.postId;
        const text   = form.querySelector('.comment-input').value.trim();
        if (!text) return;
  
        fetch(`/api/posts/${postId}/comments`, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ text })
        })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            // optionally display new comment immediately
            const list = card.querySelector('.comments-list') ||
                         createCommentsList(card);
            const li   = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = `${data.commenter}: ${data.text}`;
            list.append(li);
            form.querySelector('.comment-input').value = '';
          } else {
            alert(data.error || 'Couldn’t post comment');
          }
        })
        .catch(console.error);
      });
    }
  
    // helper to create a container for comments under a card
    function createCommentsList(card) {
      const ul = document.createElement('ul');
      ul.className = 'comments-list list-group list-group-flush mt-2';
      card.querySelector('.card-body').append(ul);
      return ul;
    }
  });
  