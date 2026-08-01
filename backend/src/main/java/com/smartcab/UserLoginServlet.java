package com.smartcab;

import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

@WebServlet("/User_Login")
public class UserLoginServlet extends HttpServlet {
    private static final long serialVersionUID = 1L;
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String email = request.getParameter("userEmail");
        String password = request.getParameter("userPassword");
        
        try {
            // Load the MySQL driver
            Class.forName("com.mysql.jdbc.Driver");
            
            // Connect to the database
            Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/SMART_CAB_SYSTEM", 
                "root", 
                "root"
            );
            
            // Prepare the SQL query
            String sql = "SELECT * FROM user_registration WHERE email = ? AND password = ?";
            PreparedStatement pstmt = conn.prepareStatement(sql);
            pstmt.setString(1, email);
            pstmt.setString(2, password);
            
            // Execute the query
            ResultSet rs = pstmt.executeQuery();
            
            if (rs.next()) {
                // Create a session
                HttpSession session = request.getSession();
                session.setAttribute("userId", rs.getString("user_id"));
                session.setAttribute("userName", rs.getString("full_name"));
                session.setAttribute("userEmail", rs.getString("email"));
                session.setAttribute("userContact", rs.getString("contact"));
                
                // Redirect to user dashboard
                response.sendRedirect("userDashboard.jsp");
            } else {
                // Invalid credentials
                request.setAttribute("errorMessage", "Invalid email or password");
                request.getRequestDispatcher("userLogin.jsp").forward(request, response);
            }
            
            // Close resources
            rs.close();
            pstmt.close();
            conn.close();
            
        } catch (Exception e) {
            e.printStackTrace();
            request.setAttribute("errorMessage", "An error occurred. Please try again.");
            request.getRequestDispatcher("userLogin.jsp").forward(request, response);
        }
    }
} 