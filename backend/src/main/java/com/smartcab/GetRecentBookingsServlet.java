package com.smartcab;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.google.gson.Gson;

@WebServlet("/GetRecentBookingsServlet")
public class GetRecentBookingsServlet extends HttpServlet {
    private static final long serialVersionUID = 1L;

    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        List<Map<String, String>> bookings = new ArrayList<>();
        Connection conn = null;
        PreparedStatement pstmt = null;
        ResultSet rs = null;

        try {
            conn = DatabaseUtil.getConnection();
            
            // Get recent bookings with user and driver information
            String sql = "SELECT b.booking_id, u.full_name as user_name, d.full_name as driver_name, " +
                        "b.pickup_location, b.dropoff_location, b.booking_date, b.booking_time, b.status " +
                        "FROM bookings b " +
                        "LEFT JOIN user_registration u ON b.user_id = u.user_id " +
                        "LEFT JOIN driver_registration d ON b.driver_id = d.driver_id " +
                        "ORDER BY b.booking_date DESC, b.booking_time DESC " +
                        "LIMIT 10";
            
            pstmt = conn.prepareStatement(sql);
            rs = pstmt.executeQuery();
            
            while (rs.next()) {
                Map<String, String> booking = new HashMap<>();
                booking.put("booking_id", rs.getString("booking_id"));
                booking.put("user_name", rs.getString("user_name"));
                booking.put("driver_name", rs.getString("driver_name"));
                booking.put("pickup_location", rs.getString("pickup_location"));
                booking.put("dropoff_location", rs.getString("dropoff_location"));
                booking.put("booking_date", rs.getString("booking_date"));
                booking.put("booking_time", rs.getString("booking_time"));
                booking.put("status", rs.getString("status"));
                bookings.add(booking);
            }

            // Convert to JSON and send response
            response.setContentType("application/json");
            response.setCharacterEncoding("UTF-8");
            response.getWriter().write(new Gson().toJson(bookings));

        } catch (Exception e) {
            e.printStackTrace();
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "Error fetching recent bookings");
        } finally {
            DatabaseUtil.closeResources(conn, pstmt, rs);
        }
    }
} 