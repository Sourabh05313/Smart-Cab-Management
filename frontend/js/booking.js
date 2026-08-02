// Import the API configuration
import { bookings, cabs } from './api.js';

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get the booking form
    const bookingForm = document.querySelector('.book-agileinfo-form form');
    
    // Add submit event listener to the form
    bookingForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = {
            fullName: document.querySelector('input[name="Name"]').value,
            phoneNumber: document.querySelector('input[name="Phone no"]').value,
            email: document.querySelector('input[name="email"]').value,
            cabType: document.querySelector('#cab').value,
            pickupDate: document.querySelector('#datepicker').value,
            pickupTime: document.querySelector('#timepicker').value,
            pickupLocation: document.querySelector('input[name="Pick-up Location"]').value,
            dropoffLocation: document.querySelector('input[name="Drop-off Location"]').value,
            passengers: document.querySelector('#passengers').value,
            direction: document.querySelector('#direction').value
        };

        try {
            // Check if user is logged in
            const token = localStorage.getItem('token');
            if (!token) {
                alert('Please login to book a cab');
                return;
            }

            // Create booking
            const response = await bookings.createBooking(formData);
            
            if (response.success) {
                alert('Booking successful! Your booking ID is: ' + response.bookingId);
                bookingForm.reset();
            } else {
                alert('Booking failed: ' + response.message);
            }
        } catch (error) {
            console.error('Error creating booking:', error);
            alert('An error occurred while creating your booking. Please try again.');
        }
    });

    // Load available cab types
    async function loadCabTypes() {
        try {
            const cabs = await cabs.getAllCabs();
            const cabSelect = document.querySelector('#cab');
            
            // Clear existing options except the first one
            while (cabSelect.options.length > 1) {
                cabSelect.remove(1);
            }
            
            // Add cab types from the backend
            cabs.forEach(cab => {
                const option = document.createElement('option');
                option.value = cab.id;
                option.textContent = cab.type;
                cabSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading cab types:', error);
        }
    }

    // Initialize date and time pickers
    $(function() {
        $("#datepicker").datepicker({
            minDate: 0, // Disable past dates
            dateFormat: 'mm/dd/yy'
        });
        
        $("#timepicker").wickedpicker({
            twentyFour: false
        });
    });

    // Load cab types when page loads
    loadCabTypes();
}); 