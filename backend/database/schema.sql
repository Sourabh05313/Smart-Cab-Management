-- Create database if not exists
CREATE DATABASE IF NOT EXISTS smart_cab_system;
USE smart_cab_system;

-- Create admin_registration table
CREATE TABLE IF NOT EXISTS admin_registration (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_name VARCHAR(100) NOT NULL,
    admin_email VARCHAR(100) NOT NULL UNIQUE,
    admin_password VARCHAR(255) NOT NULL,
    admin_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default admin
INSERT IGNORE INTO admin_registration (admin_name, admin_email, admin_password, admin_phone)
VALUES ('Admin', 'admin@smartcab.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKy7PJN9JNqZ0qK', '1234567890');

-- Create user_registration table
CREATE TABLE IF NOT EXISTS user_registration (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    user_email VARCHAR(100) NOT NULL UNIQUE,
    user_password VARCHAR(255) NOT NULL,
    user_phone VARCHAR(20),
    user_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create vehicle_types table
CREATE TABLE IF NOT EXISTS vehicle_types (
    vehicle_type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    base_fare DECIMAL(10,2) NOT NULL,
    per_km_rate DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default vehicle types
INSERT IGNORE INTO vehicle_types (type_name, base_fare, per_km_rate) VALUES 
('Sedan', 50.00, 10.00),
('SUV', 70.00, 15.00),
('Luxury', 100.00, 20.00);

-- Create driver_registration table
CREATE TABLE IF NOT EXISTS driver_registration (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    driver_name VARCHAR(100) NOT NULL,
    driver_email VARCHAR(100) NOT NULL UNIQUE,
    driver_password VARCHAR(255) NOT NULL,
    driver_phone VARCHAR(20) NOT NULL,
    driver_address TEXT,
    license_number VARCHAR(50) NOT NULL UNIQUE,
    vehicle_type_id INT,
    vehicle_number VARCHAR(20) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    current_location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
);

-- Create bookings table
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    driver_id INT,
    pickup VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    vehicle_type_id INT NOT NULL,
    status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
    fare DECIMAL(10,2),
    distance DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
    FOREIGN KEY (driver_id) REFERENCES driver_registration(driver_id),
    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    transaction_id VARCHAR(100),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);

-- Create feedback table
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    user_id INT NOT NULL,
    driver_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
    FOREIGN KEY (driver_id) REFERENCES driver_registration(driver_id)
); 