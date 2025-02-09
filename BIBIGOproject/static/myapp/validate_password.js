document.addEventListener('DOMContentLoaded', function () {
    const passwordInput = document.querySelector('input[name="password"]');
    const submitButton = document.querySelector('input[type="submit"]');

    // 創建一個紅色的錯誤提示
    const errorElement = document.createElement('div');
    errorElement.className = 
    errorElement.textContent = 'Format is incorrect';

    // 將錯誤提示添加到密碼輸入框下方
    passwordInput.parentElement.appendChild(errorElement);

    // 密碼驗證函數
    function validatePassword(password) {
        const hasUpperCase = /[A-Z]/.test(password); // 至少一個大寫字母
        const hasLowerCase = /[a-z]/.test(password); // 至少一個小寫字母
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password); // 特殊字符
        const hasMinLength = password.length >= 8; // 至少 8 個字符
        const hasSQLInjectionRisk = /['";--]/.test(password); // SQL Injection 關鍵字符

        // 綜合驗證
        return hasUpperCase && hasLowerCase && hasSpecialChar && hasMinLength && !hasSQLInjectionRisk;
    }

    // 密碼輸入框監聽事件
    passwordInput.addEventListener('input', function () {
        const password = passwordInput.value;

        if (validatePassword(password)) {
            // 驗證通過
            errorElement.style.display = 'none';
            submitButton.disabled = false;
        } else {
            // 驗證失敗
            errorElement.style.display = 'block';
            submitButton.disabled = true;
        }
    });
});
