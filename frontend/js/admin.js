import { auth } from './api.js';

document.addEventListener('DOMContentLoaded', function() {
    const adminLoginForm = document.querySelector('#adminLoginForm');
    
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                email: document.querySelector('#adminEmail').value,
                password: document.querySelector('#adminPassword').value,
                role: 'admin' // Specify this is an admin login
            };

            try {
                const response = await auth.login(formData);
                
                if (response.success) {
                    localStorage.setItem('token', response.token);
                    localStorage.setItem('userName', response.user.name);
                    localStorage.setItem('role', 'admin');
                    
                    // Redirect to admin dashboard
                    window.location.href = 'adminDashboard.html';
                } else {
                    alert('Login failed: ' + response.message);
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('An error occurred during login. Please try again.');
            }
        });
    }
}); 

/**document.addEventListener('DOMContentLoaded', function() {
    const adminLoginForm = document.querySelector('#adminLoginForm');
    
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                admin_email: document.querySelector('#adminEmail').value,
                admin_password: document.querySelector('#adminPassword').value
            };

            try {
                const response = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include', // Important for sessions
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Redirect to admin dashboard
                    window.location.href = 'adminDashboard.html';
                } else {
                    alert('Login failed: ' + (data.message || 'Invalid credentials'));
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('An error occurred during login. Please try again.');
            }
        });
    }
});**/