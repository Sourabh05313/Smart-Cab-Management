package com.smartcab;

import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@WebServlet("/UserRegistrationServlet")
public class UserRegistrationServlet extends HttpServlet {
    private static final long serialVersionUID = 1L;
    private static final String DB_URL = "jdbc:mysql://localhost:3306/SMART_CAB_SYSTEM";
    private static final String DB_USER = "root";
    private static final String DB_PASSWORD = "";

    @Override
    protected void doOptions(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        setCORSHeaders(response);
        response.setStatus(HttpServletResponse.SC_OK);
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        setCORSHeaders(response);
        response.setContentType("application/json");

        // Get parameters from request
        String fullName = request.getParameter("fullName");
        String email = request.getParameter("email");
        String password = request.getParameter("password");
        String phone = request.getParameter("phone");
        String address = request.getParameter("address");

        // Validate input
        if (fullName == null || email == null || password == null || phone == null || address == null ||
            fullName.isEmpty() || email.isEmpty() || password.isEmpty() || phone.isEmpty() || address.isEmpty()) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().write("{\"error\": \"All fields are required\"}");
            return;
        }

        Connection conn = null;
        PreparedStatement stmt = null;

        try {
            // Load MySQL driver
            Class.forName("com.mysql.cj.jdbc.Driver");
            
            // Create connection
            conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
            
            // Check if email already exists
            String checkEmailSql = "SELECT COUNT(*) FROM user_registration WHERE user_email = ?";
            PreparedStatement checkStmt = conn.prepareStatement(checkEmailSql);
            checkStmt.setString(1, email);
            if (checkStmt.executeQuery().next()) {
                response.setStatus(HttpServletResponse.SC_CONFLICT);
                response.getWriter().write("{\"error\": \"Email already registered\"}");
                return;
            }
            
            // Prepare SQL statement
            String sql = "INSERT INTO user_registration (user_name, user_email, user_password, user_phone, user_address) VALUES (?, ?, ?, ?, ?)";
            stmt = conn.prepareStatement(sql);
            stmt.setString(1, fullName);
            stmt.setString(2, email);
            stmt.setString(3, password);
            stmt.setString(4, phone);
            stmt.setString(5, address);
            
            // Execute query
            int rowsAffected = stmt.executeUpdate();
            
            if (rowsAffected > 0) {
                response.setStatus(HttpServletResponse.SC_OK);
                response.getWriter().write("{\"message\": \"Registration successful\", \"redirect\": \"userLogin.html\"}");
            } else {
                response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                response.getWriter().write("{\"error\": \"Failed to register user\"}");
            }
            
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            response.getWriter().write("{\"error\": \"Database driver not found\"}");
        } catch (SQLException e) {
            e.printStackTrace();
            if (e.getMessage().contains("Duplicate entry")) {
                response.setStatus(HttpServletResponse.SC_CONFLICT);
                response.getWriter().write("{\"error\": \"Email already registered\"}");
            } else {
                response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                response.getWriter().write("{\"error\": \"Database error: " + e.getMessage() + "\"}");
            }
        } finally {
            // Close resources
            try {
                if (stmt != null) stmt.close();
                if (conn != null) conn.close();
            } catch (SQLException e) {
                e.printStackTrace();
            }
        }
    }

    private void setCORSHeaders(HttpServletResponse response) {
        response.setHeader("Access-Control-Allow-Origin", "*");
        response.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
        response.setHeader("Access-Control-Allow-Headers", "Content-Type, Accept, Origin, Authorization");
        response.setHeader("Access-Control-Max-Age", "86400");
        response.setHeader("Access-Control-Allow-Credentials", "true");
    }
} 