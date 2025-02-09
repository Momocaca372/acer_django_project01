document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("[name='form1']");
    const errText = document.querySelector('.err_text');

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        const password = document.querySelector("[name='password']").value;

        fetch(url_path, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("[name='csrfmiddlewaretoken']").value
            },
            body: JSON.stringify({ 'password': password })
        })
            .then(response => response.json())
            .then(function (data) {
                if (!data.valid) {
                    errText.style.display = 'block';
                } else {
                    errText.style.display = 'none';
                    form.submit();
                    console.log(data.err);
                }
            })
            .catch(error => {
                console.error('error:', error);
            });
    });
});