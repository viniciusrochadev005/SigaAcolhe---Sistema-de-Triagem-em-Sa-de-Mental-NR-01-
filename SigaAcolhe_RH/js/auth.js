/**
 * Autenticação Simples Front-end
 * Como removemos o Flask, usamos localStorage para simular uma sessão.
 */

const PASSWORD_RH = "sigaacolhe2024";

document.addEventListener('DOMContentLoaded', () => {
    
    // Se estivermos na página de login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        // Se já estiver logado, redireciona pro dashboard
        if (localStorage.getItem('rh_logged_in') === 'true') {
            window.location.href = 'dashboard.html';
        }

        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const pass = document.getElementById('password').value;
            const errorDiv = document.getElementById('login-error');

            if (pass === PASSWORD_RH) {
                localStorage.setItem('rh_logged_in', 'true');
                window.location.href = 'dashboard.html';
            } else {
                errorDiv.textContent = "Senha incorreta. Tente novamente.";
                errorDiv.style.display = "block";
            }
        });
    }

    // Se estivermos no dashboard (verifica proteção)
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
        if (localStorage.getItem('rh_logged_in') !== 'true') {
            window.location.href = 'index.html';
        } else {
            // Logado: libera a interface
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', () => {
                    localStorage.removeItem('rh_logged_in');
                    window.location.href = 'index.html';
                });
            }
        }
    }
});
