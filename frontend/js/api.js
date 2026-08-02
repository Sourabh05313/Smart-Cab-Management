// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Authentication endpoints
const auth = {
    login: async (credentials) => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(credentials)
            });
            return await response.json();
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },
    register: async (userData) => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            return await response.json();
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }
};

// Cab management endpoints
const cabs = {
    getAllCabs: async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/cabs`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching cabs:', error);
            throw error;
        }
    },
    getCabById: async (id) => {
        try {
            const response = await fetch(`${API_BASE_URL}/cabs/${id}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching cab:', error);
            throw error;
        }
    }
};

// Booking endpoints
const bookings = {
    createBooking: async (bookingData) => {
        try {
            const response = await fetch(`${API_BASE_URL}/bookings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(bookingData)
            });
            return await response.json();
        } catch (error) {
            console.error('Booking error:', error);
            throw error;
        }
    },
    getUserBookings: async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/bookings/user`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            return await response.json();
        } catch (error) {
            console.error('Error fetching bookings:', error);
            throw error;
        }
    }
};

// Admin endpoints
const admin = {
    getAllUsers: async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/users`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            return await response.json();
        } catch (error) {
            console.error('Error fetching users:', error);
            throw error;
        }
    },
    getAllBookings: async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/bookings`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            return await response.json();
        } catch (error) {
            console.error('Error fetching bookings:', error);
            throw error;
        }
    }
};

// Export all API functions
export { auth, cabs, bookings, admin }; 