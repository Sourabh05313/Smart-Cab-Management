package com.smartcab;

import java.io.IOException;
import java.io.BufferedReader;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import org.json.JSONObject;

@WebServlet("/AdminLoginServlet")
public class AdminLoginServlet extends HttpServlet {
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
        PrintWriter out = response.getWriter();
        
        try {
            String email = null;
            String password = null;

            // Check content type to handle both form-urlencoded and JSON
            String contentType = request.getContentType();
            if (contentType != null && contentType.contains("application/json")) {
                // Handle JSON data
                StringBuilder sb = new StringBuilder();
                String line;
                try (BufferedReader reader = request.getReader()) {
                    while ((line = reader.readLine()) != null) {
                        sb.append(line);
                    }
                }
                JSONObject json = new JSONObject(sb.toString());
                email = json.getString("email");
                password = json.getString("password");
            } else {
                // Handle form-urlencoded data
                email = request.getParameter("email");
                password = request.getParameter("password");
            }

            if (email == null || password == null || email.isEmpty() || password.isEmpty()) {
                response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
                out.write("{\"error\": \"Email and password are required\"}");
                return;
            }

            // Test database connection first
            try {
                Class.forName("com.mysql.cj.jdbc.Driver");
            } catch (ClassNotFoundException e) {
                System.err.println("MySQL Driver not found: " + e.getMessage());
                response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                out.write("{\"error\": \"Database driver not found. Please check server configuration.\"}");
                return;
            }

            try (Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD)) {
                String sql = "SELECT * FROM admin_registration WHERE admin_email = ? AND admin_password = ?";
                try (PreparedStatement stmt = conn.prepareStatement(sql)) {
                    stmt.setString(1, email);
                    stmt.setString(2, password);
                    
                    try (ResultSet rs = stmt.executeQuery()) {
                        if (rs.next()) {
                            // Create session
                            HttpSession session = request.getSession(true);
                            session.setAttribute("admin_id", rs.getInt("admin_id"));
                            session.setAttribute("admin_name", rs.getString("admin_name"));
                            session.setAttribute("admin_email", rs.getString("admin_email"));
                            
                            // Set session timeout to 30 minutes
                            session.setMaxInactiveInterval(30 * 60);
                            
                            response.setStatus(HttpServletResponse.SC_OK);
                            out.write("{\"message\": \"Login successful\", \"redirect\": \"adminDashboard.html\"}");
                        } else {
                            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                            out.write("{\"error\": \"Invalid email or password\"}");
                        }
                    }
                }
            } catch (SQLException e) {
                System.err.println("Database error: " + e.getMessage());
                response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                out.write("{\"error\": \"Database error: " + e.getMessage() + "\"}");
            }
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            out.write("{\"error\": \"An unexpected error occurred. Please try again later.\"}");
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