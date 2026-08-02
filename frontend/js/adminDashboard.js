$(document).ready(function() {
    // Configure jQuery AJAX defaults
    $.ajaxSetup({
        xhrFields: {
            withCredentials: true
        }
    });

    // Check admin session on page load
    checkAdminSession();

    // Initialize tab functionality
    $('.list-group-item').click(function(e) {
        e.preventDefault();
        $(this).tab('show');
    });
});

// Check admin session
async function checkAdminSession() {
    try {
        const response = await fetch('http://localhost:5000/api/admin/session', {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Session is valid, load dashboard
            loadDashboardStats();
            loadRecentBookings();
            return true;
        } else {
            // No valid session, redirect to login
            window.location.href = 'adminLogin.html';
            return false;
        }
    } catch (error) {
        console.error('Error checking session:', error);
        window.location.href = 'adminLogin.html';
        return false;
    }
}

// Load dashboard statistics
async function loadDashboardStats() {
    if (!await checkAdminSession()) return;
    
    try {
        const response = await fetch('http://localhost:5000/api/admin/stats', {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            $('#totalUsers').text(data.stats.total_users);
            $('#totalDrivers').text(data.stats.total_drivers);
            $('#totalBookings').text(data.stats.total_bookings);
            $('#totalRevenue').text(`₹${data.stats.total_revenue}`);
        } else {
            console.error('Failed to load stats:', data.message);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load recent bookings
async function loadRecentBookings() {
    if (!await checkAdminSession()) return;
    
    try {
        const response = await fetch('http://localhost:5000/api/admin/recent-bookings', {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            const tbody = $('#recentBookingsTableBody');
            tbody.empty();
            
            if (data.bookings && data.bookings.length > 0) {
                data.bookings.forEach(booking => {
                    tbody.append(`
                        <tr>
                            <td>${booking.booking_id}</td>
                            <td>${booking.user_name}</td>
                            <td>${booking.pickup_location}</td>
                            <td>${booking.dropoff_location}</td>
                            <td>₹${booking.fare}</td>
                            <td>${booking.status}</td>
                        </tr>
                    `);
                });
            } else {
                tbody.append('<tr><td colspan="6" class="text-center">No recent bookings found</td></tr>');
            }
        } else {
            console.error('Failed to load recent bookings:', data.message);
        }
    } catch (error) {
        console.error('Error loading recent bookings:', error);
    }
}

// Load all bookings
async function loadAllBookings() {
    if (!await checkAdminSession()) return;
    
    try {
        const response = await fetch('http://localhost:5000/api/admin/bookings', {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const tbody = $('#allBookings');
            tbody.empty();
            
            if (data.bookings && data.bookings.length > 0) {
                data.bookings.forEach(booking => {
                    const row = `
                        <tr>
                            <td>${booking.booking_id}</td>
                            <td>${booking.user_name}</td>
                            <td>${booking.driver_name || 'Not Assigned'}</td>
                            <td>${booking.pickup_location}</td>
                            <td>${booking.destination}</td>
                            <td>${booking.booking_date}</td>
                            <td>${booking.booking_time}</td>
                            <td>
                                <span class="badge bg-${getStatusBadgeClass(booking.status)}">
                                    ${booking.status}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="updateBookingStatus(${booking.booking_id}, 'confirmed')">
                                    <i class="fas fa-check"></i> Confirm
                                </button>
                                <button class="btn btn-sm btn-success" onclick="updateBookingStatus(${booking.booking_id}, 'completed')">
                                    <i class="fas fa-flag-checkered"></i> Complete
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="updateBookingStatus(${booking.booking_id}, 'cancelled')">
                                    <i class="fas fa-times"></i> Cancel
                                </button>
                            </td>
                        </tr>
                    `;
                    tbody.append(row);
                });
            } else {
                tbody.append('<tr><td colspan="9" class="text-center">No bookings found</td></tr>');
            }
        } else {
            showError(data.message || 'Failed to load bookings');
        }
    } catch (error) {
        console.error('Error loading bookings:', error);
        showError('Failed to load bookings. Please try again.');
    }
}

// Load users
async function loadUsers() {
    if (!await checkAdminSession()) return;
    
    try {
        const response = await fetch('http://localhost:5000/api/admin/users', {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const tbody = $('#usersTableBody');
            tbody.empty();
            
            if (data.users && data.users.length > 0) {
                data.users.forEach(user => {
                    const row = `
                        <tr>
                            <td>${user.user_id}</td>
                            <td>${user.user_name}</td>
                            <td>${user.user_email}</td>
                            <td>${user.user_phone || '-'}</td>
                            <td>${user.user_address || '-'}</td>
                            <td>${new Date(user.created_at).toLocaleString()}</td>
                            <td>
                                <button class="btn btn-sm btn-info" onclick="viewUserDetails(${user.user_id})">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.user_id})">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </td>
                        </tr>
                    `;
                    tbody.append(row);
                });
            } else {
                tbody.append('<tr><td colspan="7" class="text-center">No users found</td></tr>');
            }
        } else {
            showError(data.message || 'Failed to load users');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Failed to load users. Please try again.');
    }
}

// Update booking status
async function updateBookingStatus(bookingId, status) {
    if (!await checkAdminSession()) return;
    
    if (!confirm(`Are you sure you want to ${status} this booking?`)) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/admin/bookings/${bookingId}`, {
            method: 'PUT',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ status })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess(`Booking ${status} successfully`);
            loadAllBookings();
        } else {
            showError(data.message || 'Failed to update booking status');
        }
    } catch (error) {
        console.error('Error updating booking status:', error);
        showError('Failed to update booking status. Please try again.');
    }
}

// View user details
async function viewUserDetails(userId) {
    if (!await checkAdminSession()) return;
    
    try {
        const response = await fetch(`http://localhost:5000/api/admin/users/${userId}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            const user = data.user;
            $('#userDetailsModal .modal-body').html(`
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Name:</strong> ${user.user_name}</p>
                        <p><strong>Email:</strong> ${user.user_email}</p>
                        <p><strong>Phone:</strong> ${user.user_phone || '-'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Address:</strong> ${user.user_address || '-'}</p>
                        <p><strong>Created At:</strong> ${new Date(user.created_at).toLocaleString()}</p>
                    </div>
                </div>
            `);
            $('#userDetailsModal').modal('show');
        } else {
            showError(data.message || 'Failed to load user details');
        }
    } catch (error) {
        console.error('Error loading user details:', error);
        showError('Failed to load user details. Please try again.');
    }
}

// Delete user
async function deleteUser(userId) {
    if (!await checkAdminSession()) return;
    
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/admin/users/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess('User deleted successfully');
            loadUsers();
        } else {
            showError(data.message || 'Failed to delete user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showError('Failed to delete user. Please try again.');
    }
}

// Get status badge class
function getStatusBadgeClass(status) {
    switch (status.toLowerCase()) {
        case 'pending':
            return 'warning';
        case 'confirmed':
            return 'info';
        case 'completed':
            return 'success';
        case 'cancelled':
            return 'danger';
        default:
            return 'secondary';
    }
}

// Load drivers
async function loadDrivers() {
    if (!await checkAdminSession()) return;
    
    try {
        const response = await fetch('http://localhost:5000/api/admin/drivers', {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const tbody = $('#driversTableBody');
            tbody.empty();
            
            if (data.drivers && data.drivers.length > 0) {
                data.drivers.forEach(driver => {
                    const row = `
                        <tr>
                            <td>${driver.driver_id}</td>
                            <td>${driver.driver_name}</td>
                            <td>${driver.driver_email}</td>
                            <td>${driver.driver_phone || '-'}</td>
                            <td>${driver.license_number || '-'}</td>
                            <td>${driver.vehicle_number || '-'}</td>
                            <td>
                                <span class="badge bg-${driver.is_available ? 'success' : 'danger'}">
                                    ${driver.is_available ? 'Available' : 'Unavailable'}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-info" onclick="viewDriverDetails(${driver.driver_id})">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="deleteDriver(${driver.driver_id})">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </td>
                        </tr>
                    `;
                    tbody.append(row);
                });
            } else {
                tbody.append('<tr><td colspan="8" class="text-center">No drivers found</td></tr>');
            }
        } else {
            showError(data.message || 'Failed to load drivers');
        }
    } catch (error) {
        console.error('Error loading drivers:', error);
        showError('Failed to load drivers. Please try again.');
    }
}

// Logout
function logout() {
    fetch('http://localhost:5000/api/admin/logout', {
        method: 'POST',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = 'adminLogin.html';
        } else {
            showError(data.message || 'Failed to logout');
        }
    })
    .catch(error => {
        console.error('Error logging out:', error);
        showError('Failed to logout. Please try again.');
    });
}

// Show success message
function showSuccess(message) {
    const alert = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    $('#alerts').append(alert);
    setTimeout(() => $('.alert').alert('close'), 5000);
}

// Show error message
function showError(message) {
    const alert = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    $('#alerts').append(alert);
    setTimeout(() => $('.alert').alert('close'), 5000);
}
