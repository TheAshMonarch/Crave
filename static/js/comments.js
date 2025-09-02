document.addEventListener('DOMContentLoaded', function () {
    const commentForm = document.querySelector('form[action*="/add_comment/"]');
    if (commentForm) {
        commentForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(commentForm);
            fetch(commentForm.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.querySelector('.comments-list').innerHTML = data.html;
                    commentForm.querySelector('textarea[name="comment"]').value = '';
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
});