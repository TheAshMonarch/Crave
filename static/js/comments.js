document.addEventListener('DOMContentLoaded', function () {
  // Helper toast (works with #toast in recipe pages, or falls back to alert)
  function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    if (!toast) { alert(message); return; }
    toast.textContent = message;
    toast.classList.remove('hidden', isError ? 'bg-green-500' : 'bg-red-500');
    toast.classList.add(isError ? 'bg-red-500' : 'bg-green-500');
    setTimeout(() => toast.classList.add('hidden'), 3000);
  }

  // Add comment (AJAX)
  const commentForm = document.querySelector('form.comment-form, form[action*="/add_comment/"]');
  if (commentForm) {
    commentForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const btn = commentForm.querySelector('button[type="submit"]');
      const original = btn ? btn.textContent : null;
      if (btn) { btn.textContent = 'Posting...'; btn.disabled = true; }

      try {
        const formData = new FormData(commentForm); // includes csrf_token + comment_text
        const resp = await fetch(commentForm.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          body: formData
        });
        const data = await resp.json();

        if (data.success) {
          // Replace comments list HTML
          const container = document.getElementById('comments-container');
          if (container && data.html) container.innerHTML = data.html;

          // Clear textarea
          const textarea = commentForm.querySelector('textarea[name="comment_text"]');
          if (textarea) textarea.value = '';

          showToast(data.message || 'Comment added successfully!');
        } else {
          showToast(data.error || 'Error adding comment', true);
        }
      } catch (err) {
        console.error(err);
        showToast('An error occurred', true);
      } finally {
        if (btn) { btn.textContent = original; btn.disabled = false; }
      }
    });
  }

  // Delete comment (delegated)
  document.addEventListener('submit', async (e) => {
    const form = e.target;
    if (!form.classList.contains('delete-comment-form')) return;

    e.preventDefault();
    try {
      const resp = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await resp.json();
      if (data.success) {
        const container = document.getElementById('comments-container');
        if (container && data.html) container.innerHTML = data.html;
        showToast(data.message || 'Comment deleted');
      } else {
        showToast(data.error || 'Error deleting comment', true);
      }
    } catch (err) {
      console.error(err);
      showToast('An error occurred', true);
    }
  });
});
