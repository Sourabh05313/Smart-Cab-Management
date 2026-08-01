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

@WebServlet("/DriverManagementServlet")
public class DriverManagementServlet extends HttpServlet {
    private static final long serialVersionUID = 1L;

    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        List<Map<String, String>> drivers = new ArrayList<>();
        Connection conn = null;
        PreparedStatement pstmt = null;
        ResultSet rs = null;

        try {
            conn = DatabaseUtil.getConnection();
            
            // Get all drivers with their details
            String sql = "SELECT driver_id, full_name, email, phone, license_number, " +
                        "vehicle_number, vehicle_type, status, rating " +
                        "FROM driver_registration " +
                        "ORDER BY status DESC, full_name ASC";
            
            pstmt = conn.prepareStatement(sql);
            rs = pstmt.executeQuery();
            
            while (rs.next()) {
                Map<String, String> driver = new HashMap<>();
                driver.put("driver_id", rs.getString("driver_id"));
                driver.put("full_name", rs.getString("full_name"));
                driver.put("email", rs.getString("email"));
                driver.put("phone", rs.getString("phone"));
                driver.put("license_number", rs.getString("license_number"));
                driver.put("vehicle_number", rs.getString("vehicle_number"));
                driver.put("vehicle_type", rs.getString("vehicle_type"));
                driver.put("status", rs.getString("status"));
                driver.put("rating", rs.getString("rating"));
                drivers.add(driver);
            }

            // Convert to JSON and send response
            response.setContentType("application/json");
            response.setCharacterEncoding("UTF-8");
            response.getWriter().write(new Gson().toJson(drivers));

        } catch (Exception e) {
            e.printStackTrace();
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "Error fetching driver information");
        } finally {
            DatabaseUtil.closeResources(conn, pstmt, rs);
        }
    }

    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        String action = request.getParameter("action");
        String driverId = request.getParameter("driver_id");
        
        if (action == null || driverId == null) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Missing required parameters");
            return;
        }

        Connection conn = null;
        PreparedStatement pstmt = null;

        try {
            conn = DatabaseUtil.getConnection();
            String sql = "";

            switch (action) {
                case "activate":
                    sql = "UPDATE driver_registration SET status = 'active' WHERE driver_id = ?";
                    break;
                case "deactivate":
                    sql = "UPDATE driver_registration SET status = 'inactive' WHERE driver_id = ?";
                    break;
                case "delete":
                    sql = "DELETE FROM driver_registration WHERE driver_id = ?";
                    break;
                default:
                    response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid action");
                    return;
            }

            pstmt = conn.prepareStatement(sql);
            pstmt.setString(1, driverId);
            int rowsAffected = pstmt.executeUpdate();

            if (rowsAffected > 0) {
                response.setStatus(HttpServletResponse.SC_OK);
                response.getWriter().write("{\"success\": true}");
            } else {
                response.sendError(HttpServletResponse.SC_NOT_FOUND, "Driver not found");
            }

        } catch (Exception e) {
            e.printStackTrace();
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "Error processing request");
        } finally {
            DatabaseUtil.closeResources(conn, pstmt, null);
        }
    }
} 