package com.smartcab;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.HashMap;
import java.util.Map;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.google.gson.Gson;

@WebServlet("/GetDashboardStatsServlet")
public class GetDashboardStatsServlet extends HttpServlet {
    private static final long serialVersionUID = 1L;

    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        Map<String, Integer> stats = new HashMap<>();
        Connection conn = null;
        PreparedStatement pstmt = null;
        ResultSet rs = null;

        try {
            conn = DatabaseUtil.getConnection();
            
            // Get total bookings
            pstmt = conn.prepareStatement("SELECT COUNT(*) FROM bookings");
            rs = pstmt.executeQuery();
            if (rs.next()) {
                stats.put("totalBookings", rs.getInt(1));
            }
            
            // Get active drivers
            pstmt = conn.prepareStatement("SELECT COUNT(*) FROM driver_registration WHERE status = 'active'");
            rs = pstmt.executeQuery();
            if (rs.next()) {
                stats.put("activeDrivers", rs.getInt(1));
            }
            
            // Get total users
            pstmt = conn.prepareStatement("SELECT COUNT(*) FROM user_registration");
            rs = pstmt.executeQuery();
            if (rs.next()) {
                stats.put("totalUsers", rs.getInt(1));
            }

            // Convert to JSON and send response
            response.setContentType("application/json");
            response.setCharacterEncoding("UTF-8");
            response.getWriter().write(new Gson().toJson(stats));

        } catch (Exception e) {
            e.printStackTrace();
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "Error fetching dashboard statistics");
        } finally {
            DatabaseUtil.closeResources(conn, pstmt, rs);
        }
    }
} 