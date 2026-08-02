// Import the API configuration
import { auth } from './api.js';

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get the login and register forms
    const loginForm = document.querySelector('#loginForm');
    const registerForm = document.querySelector('#registerForm');
    const logoutBtn = document.querySelector('#logoutBtn');
    const authSection = document.querySelector('.top-forms');

    // Function to update UI based on auth state
    function updateAuthUI() {
        const token = localStorage.getItem('token');
        const userName = localStorage.getItem('userName');

        if (token && userName) {
            // User is logged in
            authSection.innerHTML = `
                <span class="mx-lg-4 mx-md-2 mx-1">
                    <a href="#" id="userProfile">
                        <i class="fas fa-user"></i> ${userName}
                    </a>
                </span>
                <span>
                    <a href="#" id="logoutBtn">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </a>
                </span>
            `;
        } else {
            // User is not logged in
            authSection.innerHTML = `
                <span class="mx-lg-4 mx-md-2 mx-1">
                    <a href="#" data-toggle="modal" data-target="#loginModal">
                        <i class="fas fa-lock"></i> Login
                    </a>
                </span>
                <span>
                    <a href="#" data-toggle="modal" data-target="#registerModal">
                        <i class="fas fa-user"></i> Register
                    </a>
                </span>
            `;
        }

        // Re-attach event listeners
        attachAuthEventListeners();
    }

    // Function to attach event listeners for auth elements
    function attachAuthEventListeners() {
        const newLogoutBtn = document.querySelector('#logoutBtn');
        if (newLogoutBtn) {
            newLogoutBtn.addEventListener('click', handleLogout);
        }
    }

    // Handle login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                email: document.querySelector('#loginEmail').value,
                password: document.querySelector('#loginPassword').value
            };

            try {
                const response = await auth.login(formData);
                
                if (response.success) {
                    localStorage.setItem('token', response.token);
                    localStorage.setItem('userName', response.user.name);
                    
                    // Close the login modal
                    $('#loginModal').modal('hide');
                    
                    // Update UI
                    updateAuthUI();
                    
                    alert('Login successful!');
                } else {
                    alert('Login failed: ' + response.message);
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('An error occurred during login. Please try again.');
            }
        });
    }

    // Handle register form submission
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                name: document.querySelector('#registerName').value,
                email: document.querySelector('#registerEmail').value,
                password: document.querySelector('#registerPassword').value,
                phoneNumber: document.querySelector('#registerPhone').value
            };

            try {
                const response = await auth.register(formData);
                
                if (response.success) {
                    // Close the register modal
                    $('#registerModal').modal('hide');
                    
                    alert('Registration successful! Please login to continue.');
                } else {
                    alert('Registration failed: ' + response.message);
                }
            } catch (error) {
                console.error('Registration error:', error);
                alert('An error occurred during registration. Please try again.');
            }
        });
    }

    // Handle logout
    async function handleLogout(e) {
        e.preventDefault();
        
        // Clear local storage
        localStorage.removeItem('token');
        localStorage.removeItem('userName');
        
        // Update UI
        updateAuthUI();
        
        alert('Logged out successfully!');
    }

    // Initialize UI based on auth state
    updateAuthUI();
}); 