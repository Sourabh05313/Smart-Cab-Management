-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS SMART_CAB_SYSTEM;

-- Use the database
USE SMART_CAB_SYSTEM;

-- Drop existing tables if they exist (to avoid conflicts)
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS driver_registration;
DROP TABLE IF EXISTS vehicle_types;
DROP TABLE IF EXISTS admin_registration;
DROP TABLE IF EXISTS user_registration;

-- Create admin_registration table
CREATE TABLE IF NOT EXISTS admin_registration (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_name VARCHAR(100) NOT NULL,
    admin_email VARCHAR(100) NOT NULL UNIQUE,
    admin_password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin
INSERT INTO admin_registration (admin_name, admin_email, admin_password) 
VALUES ('Admin', 'admin@gmail.com', 'admin123');

-- Create user_registration table
CREATE TABLE IF NOT EXISTS user_registration (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    user_email VARCHAR(100) NOT NULL UNIQUE,
    user_password VARCHAR(100) NOT NULL,
    user_phone VARCHAR(20) NOT NULL,
    user_address TEXT NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create vehicle_types table
CREATE TABLE IF NOT EXISTS vehicle_types (
    vehicle_type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    base_fare DECIMAL(10,2) NOT NULL,
    per_km_rate DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert vehicle types
INSERT INTO vehicle_types (type_name, base_fare, per_km_rate) VALUES 
('Sedan', 50.00, 10.00),
('SUV', 70.00, 15.00),
('Luxury', 100.00, 20.00);

-- Create driver_registration table
CREATE TABLE IF NOT EXISTS driver_registration (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    driver_name VARCHAR(100) NOT NULL,
    driver_email VARCHAR(100) NOT NULL UNIQUE,
    driver_password VARCHAR(100) NOT NULL,
    driver_phone VARCHAR(20) NOT NULL,
    driver_license VARCHAR(50) NOT NULL,
    vehicle_number VARCHAR(20) NOT NULL,
    vehicle_type_id INT NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
);

-- Create bookings table
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    driver_id INT,
    pickup_location VARCHAR(255) NOT NULL,
    dropoff_location VARCHAR(255) NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    vehicle_type_id INT NOT NULL,
    status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
    fare DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
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

-- Insert sample data
-- Sample users
INSERT INTO user_registration (user_name, user_email, user_password, user_phone, user_address) VALUES
('John Doe', 'john@example.com', 'password123', '1234567890', '123 Main St'),
('Jane Smith', 'jane@example.com', 'password123', '0987654321', '789 Oak St');

-- Sample drivers
INSERT INTO driver_registration (driver_name, driver_email, driver_password, driver_phone, driver_license, vehicle_number, vehicle_type_id) VALUES
('Mike Johnson', 'mike@example.com', 'password123', '1112223333', 'DL123456', 'MH12AB1234', 1),
('Sarah Williams', 'sarah@example.com', 'password123', '4445556666', 'DL789012', 'MH12CD5678', 2);

-- Sample bookings
INSERT INTO bookings (user_id, driver_id, pickup_location, dropoff_location, booking_date, booking_time, vehicle_type_id, status, fare) VALUES
(1, 1, '123 Main St', '456 Park Ave', '2023-04-20', '10:00:00', 1, 'completed', 25.50),
(2, 2, '789 Oak St', '321 Pine St', '2023-04-21', '15:30:00', 2, 'completed', 30.75);

-- Sample payments
INSERT INTO payments (booking_id, amount, payment_method, payment_status, transaction_id) VALUES
(1, 25.50, 'Credit Card', 'completed', 'TXN123456'),
(2, 30.75, 'Cash', 'completed', 'TXN789012');

-- Sample reviews
INSERT INTO reviews (booking_id, user_id, driver_id, rating, comment) VALUES
(1, 1, 1, 5, 'Great service! Very professional driver.'),
(2, 2, 2, 4, 'Good experience overall, would recommend.'); 