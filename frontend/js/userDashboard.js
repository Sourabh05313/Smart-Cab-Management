$(document).ready(function() {
    // Initialize tab functionality
    function showDashboard() {
        $('#dashboardContent').show();
        $('#myBookingsContent').hide();
        $('#profileContent').hide();
        $('#pageTitle').text('Dashboard');
    }

    function showMyBookings() {
        $('#dashboardContent').hide();
        $('#myBookingsContent').show();
        $('#profileContent').hide();
        $('#pageTitle').text('My Bookings');
        loadBookings();
    }

    function showProfile() {
        $('#dashboardContent').hide();
        $('#myBookingsContent').hide();
        $('#profileContent').show();
        $('#pageTitle').text('Profile');
    }

    $('.list-group-item').click(function(e) {
        e.preventDefault();
        $(this).tab('show');
    });

    // Load user's bookings
    async function loadBookings() {
        try {
            showLoading();
            const response = await fetch('/api/user/bookings', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            const data = await response.json();
            const tbody = $('#myBookingsTableBody');
            tbody.empty();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to load bookings');
            }
            
            if (data.bookings && data.bookings.length > 0) {
                data.bookings.forEach(booking => {
                    const row = `
                        <tr>
                            <td>${booking.id}</td>
                            <td>${booking.pickup_location}</td>
                            <td>${booking.dropoff_location}</td>
                            <td>${booking.booking_date}</td>
                            <td>${booking.booking_time}</td>
                            <td>${booking.vehicle_type || 'Standard'}</td>
                            <td>
                                <span class="badge bg-${getStatusBadgeClass(booking.status)}">
                                    ${booking.status}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-info" onclick="viewBooking(${booking.id})">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                ${booking.status === 'pending' ? 
                                    `<button class="btn btn-sm btn-danger" onclick="cancelBooking(${booking.id})">
                                        <i class="fas fa-times"></i> Cancel
                                    </button>` : 
                                    ''
                                }
                            </td>
                        </tr>
                    `;
                    tbody.append(row);
                });
            } else {
                tbody.append('<tr><td colspan="8" class="text-center">No bookings found</td></tr>');
            }
            hideLoading();
        } catch (error) {
            console.error('Error loading bookings:', error);
            hideLoading();
            showError(error.message || 'Failed to load bookings. Please try again.');
        }
    }

    // Load bookings when My Bookings tab is clicked
    $('a[href="#myBookings"]').click(function() {
        loadBookings();
    });

    // Handle booking cancellation
    $(document).on('click', '.cancel-booking', async function() {
        const bookingId = $(this).data('id');
        if (confirm('Are you sure you want to cancel this booking?')) {
            try {
                const response = await fetch(`/api/user/bookings/${bookingId}`, {
                    method: 'DELETE',
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Failed to cancel booking');
                }
                
                const data = await response.json();
                if (data.success) {
                    showSuccess('Booking cancelled successfully');
                    loadBookings();
                } else {
                    throw new Error(data.message || 'Failed to cancel booking');
                }
            } catch (error) {
                console.error('Error cancelling booking:', error);
                showError('Failed to cancel booking. Please try again.');
            }
        }
    });

    // Handle feedback submission
    $(document).on('click', '.give-feedback', function() {
        const bookingId = $(this).data('id');
        $('#feedbackBookingId').val(bookingId);
        $('#feedbackModal').modal('show');
    });

    // Submit feedback
    $('#feedbackForm').on('submit', async function(e) {
        e.preventDefault();
        
        const bookingId = $('#feedbackBookingId').val();
        const rating = $('#rating').val();
        const comment = $('#comment').val();
        
        try {
            const response = await fetch(`/api/user/bookings/${bookingId}/feedback`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ rating, comment })
            });
            
            if (!response.ok) {
                throw new Error('Failed to submit feedback');
            }
            
            const data = await response.json();
            if (data.success) {
                showSuccess('Feedback submitted successfully');
                $('#feedbackModal').modal('hide');
                $('#feedbackForm')[0].reset();
            } else {
                throw new Error(data.message || 'Failed to submit feedback');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            showError('Failed to submit feedback. Please try again.');
        }
    });

    // Helper function to get badge class based on status
    function getStatusBadgeClass(status) {
        switch(status.toLowerCase()) {
            case 'pending':
                return 'warning';
            case 'confirmed':
                return 'success';
            case 'cancelled':
                return 'danger';
            case 'completed':
                return 'info';
            default:
                return 'secondary';
        }
    }

    // Helper function to show success message
    function showSuccess(message) {
        const successDiv = $('#successMessage');
        successDiv.text(message);
        successDiv.removeClass('d-none');
        setTimeout(() => successDiv.addClass('d-none'), 5000);
    }

    // Helper function to show error message
    function showError(message) {
        const errorDiv = $('#errorMessage');
        errorDiv.text(message);
        errorDiv.removeClass('d-none');
        setTimeout(() => errorDiv.addClass('d-none'), 5000);
    }

    // Handle profile update
    $('form[action="UpdateProfileServlet"]').submit(function(e) {
        e.preventDefault();
        const formData = $(this).serialize();
        
        $.ajax({
            url: 'UpdateProfileServlet',
            method: 'POST',
            data: formData,
            success: function(response) {
                alert('Profile updated successfully');
            }
        });
    });

    // Vehicle type rates
    const vehicleRates = {
        'Sedan': { base: 50.00, perKm: 10.00 },
        'SUV': { base: 70.00, perKm: 15.00 },
        'Luxury': { base: 100.00, perKm: 20.00 }
    };

    // Calculate fare based on distance and vehicle type
    function calculateFare(distance, vehicleType) {
        const rates = vehicleRates[vehicleType];
        if (!rates) return 0;
        return rates.base + (distance * rates.perKm);
    }

    // Update fare when distance or vehicle type changes
    $('#distance, #vehicleType').on('change', function() {
        const distance = parseFloat($('#distance').val()) || 0;
        const vehicleType = $('#vehicleType').val();
        if (distance > 0 && vehicleType) {
            const fare = calculateFare(distance, vehicleType);
            $('#fare').val(fare.toFixed(2));
        } else {
            $('#fare').val('');
        }
    });

    // Handle ride booking with better validation
    $('#quickBookForm').on('submit', async function(e) {
        e.preventDefault();
        
        // Clear previous error messages
        $('.is-invalid').removeClass('is-invalid');
        $('.invalid-feedback').remove();
        
        // Get form values
        const formData = {
            pickup_location: $('#pickupLocation').val().trim(),
            destination: $('#destination').val().trim(),
            date: $('#bookingDate').val().trim(),
            time: $('#bookingTime').val().trim(),
            vehicle_type: $('#vehicleType').val().trim()
        };

        // Validate required fields
        let isValid = true;
        
        if (!formData.pickup_location) {
            showFieldError('pickupLocation', 'Pickup location is required');
            isValid = false;
        }
        
        if (!formData.destination) {
            showFieldError('destination', 'Destination is required');
            isValid = false;
        }
        
        if (!formData.date) {
            showFieldError('bookingDate', 'Date is required');
            isValid = false;
        } else if (!isValidDate(formData.date)) {
            showFieldError('bookingDate', 'Please select a valid future date in YYYY-MM-DD format');
            isValid = false;
        }
        
        if (!formData.time) {
            showFieldError('bookingTime', 'Time is required');
            isValid = false;
        } else if (!isValidTime(formData.time)) {
            showFieldError('bookingTime', 'Please enter time in 12-hour format (e.g., 02:30 PM)');
            isValid = false;
        }
        
        if (!formData.vehicle_type) {
            showFieldError('vehicleType', 'Vehicle type is required');
            isValid = false;
        }

        if (!isValid) {
            showError('Please fill all required fields correctly');
            return;
        }

        // Format time to ensure consistent format
        formData.time = formatTime(formData.time);

        try {
            const response = await fetch('/api/user/bookings', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to create booking');
            }

            showSuccess('Booking created successfully! Your booking ID: ' + data.booking_id);
            $('#quickBookForm')[0].reset();
            $('#fare').val('');
            loadBookings();
        } catch (error) {
            console.error('Booking error:', error);
            showError(error.message || 'Failed to create booking. Please try again.');
        }
    });

    // Helper function to show field-specific errors
    function showFieldError(fieldId, message) {
        const $field = $('#' + fieldId);
        $field.addClass('is-invalid');
        
        if ($field.next('.invalid-feedback').length === 0) {
            $field.after(`<div class="invalid-feedback">${message}</div>`);
        } else {
            $field.next('.invalid-feedback').text(message);
        }
    }

    // Validate date format and ensure it's in the future
    function isValidDate(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return date >= today;
    }

    // Validate time format (12-hour with AM/PM)
    function isValidTime(timeString) {
        // Convert to uppercase for consistency
        timeString = timeString.toUpperCase();
        
        // Strict 12-hour format validation
        const timeRegex = /^(0?[1-9]|1[0-2]):[0-5][0-9]\s*[AP]M$/;
        if (!timeRegex.test(timeString)) {
            return false;
        }
        
        // Additional validation for hours and minutes
        const [time, period] = timeString.split(/\s+/);
        const [hours, minutes] = time.split(':');
        
        const hour = parseInt(hours);
        const minute = parseInt(minutes);
        
        return hour >= 1 && hour <= 12 && minute >= 0 && minute <= 59;
    }

    // View booking details
    async function viewBooking(bookingId) {
        try {
            showLoading();
            const response = await fetch(`/api/user/bookings/${bookingId}`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const booking = await response.json();
                alert(`
                    Booking Details:
                    ID: ${booking.id}
                    Pickup: ${booking.pickup_location}
                    Destination: ${booking.destination}
                    Date: ${booking.date}
                    Time: ${booking.time}
                    Status: ${booking.status}
                    Vehicle Type: ${booking.vehicle_type || 'Standard'}
                `);
            } else {
                throw new Error('Failed to load booking details');
            }
            hideLoading();
        } catch (error) {
            console.error('Error viewing booking:', error);
            hideLoading();
            showError(error.message || 'Failed to load booking details');
        }
    }

    // Cancel booking
    async function cancelBooking(bookingId) {
        if (!confirm('Are you sure you want to cancel this booking?')) {
            return;
        }

        try {
            showLoading();
            const response = await fetch(`/api/user/bookings/${bookingId}/cancel`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                showSuccess('Booking cancelled successfully');
                loadBookings();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to cancel booking');
            }
            hideLoading();
        } catch (error) {
            console.error('Error cancelling booking:', error);
            hideLoading();
            showError(error.message || 'Failed to cancel booking');
        }
    }

    // Show loading spinner
    function showLoading() {
        $('#loadingSpinner').show();
    }

    // Hide loading spinner
    function hideLoading() {
        $('#loadingSpinner').hide();
    }

    // Load bookings when page loads
    loadBookings();

    // Add new helper function to format time consistently
    function formatTime(timeString) {
        // Convert to uppercase for consistency
        timeString = timeString.toUpperCase();
        
        // Ensure space between time and AM/PM
        timeString = timeString.replace(/(\d)([AP]M)/, '$1 $2');
        
        // Add leading zero if needed
        const parts = timeString.split(':');
        if (parts[0].length === 1) {
            parts[0] = '0' + parts[0];
        }
        
        return parts.join(':');
    }
});