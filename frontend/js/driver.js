import { auth } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const driverLoginForm = document.getElementById('driverLoginForm');
    
    if (driverLoginForm) {
        driverLoginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('driverEmail').value;
            const password = document.getElementById('driverPassword').value;
            
            try {
                const response = await auth.login({
                    email,
                    password,
                    role: 'driver'
                });
                
                if (response.token) {
                    localStorage.setItem('token', response.token);
                    localStorage.setItem('user', JSON.stringify(response.user));
                    window.location.href = 'driverDashboard.html';
                } else {
                    alert('Login failed. Please check your credentials.');
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('An error occurred during login. Please try again.');
            }
        });
    }
}); 