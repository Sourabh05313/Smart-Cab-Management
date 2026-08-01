from flask import Blueprint, jsonify, request, session
from ..utils.database import get_db_connection
from datetime import datetime
from functools import wraps

bp = Blueprint('booking', __name__, url_prefix='/api/user')

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'User authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/bookings', methods=['GET'])
@user_required
def get_user_bookings():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT b.*, vt.type_name as vehicle_type_name
            FROM bookings b
            LEFT JOIN vehicle_types vt ON b.vehicle_type_id = vt.vehicle_type_id
            WHERE b.user_id = %s
            ORDER BY b.booking_date DESC, b.booking_time DESC
        """, (session['user_id'],))
        
        bookings = cursor.fetchall()
        
        # Format the response
        formatted_bookings = []
        for booking in bookings:
            formatted_bookings.append({
                'id': booking['booking_id'],
                'pickup_location': booking['pickup_location'],
                'destination': booking['destination'],
                'date': booking['booking_date'].strftime('%Y-%m-%d'),
                'time': booking['booking_time'].strftime('%H:%M'),
                'status': booking['status'],
                'vehicle_type': booking['vehicle_type_name']
            })
        
        return jsonify({'bookings': formatted_bookings})
        
    except Exception as e:
        print(f"Error getting bookings: {str(e)}")
        return jsonify({'error': 'Failed to get bookings'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@bp.route('/bookings', methods=['POST'])
@user_required
def create_booking():
    try:
        data = request.get_json()
        print("Received booking data:", data)  # Debug log
        
        # Extract and validate required fields
        pickup_location = data.get('pickup_location')
        destination = data.get('destination')
        date = data.get('date')
        time = data.get('time')
        vehicle_type = data.get('vehicle_type')
        
        # Log the extracted values
        print(f"Extracted values - pickup: {pickup_location}, destination: {destination}, date: {date}, time: {time}, vehicle: {vehicle_type}")
        
        # Validate required fields
        if not pickup_location:
            return jsonify({'error': 'Missing required field: pickup_location'}), 400
        if not destination:
            return jsonify({'error': 'Missing required field: destination'}), 400
        if not date:
            return jsonify({'error': 'Missing required field: date'}), 400
        if not time:
            return jsonify({'error': 'Missing required field: time'}), 400
        if not vehicle_type:
            return jsonify({'error': 'Missing required field: vehicle_type'}), 400
        
        # Parse date and time
        try:
            booking_date = datetime.strptime(date, '%Y-%m-%d').date()
            booking_time = datetime.strptime(time, '%H:%M').time()
        except ValueError as e:
            print(f"Date/time parsing error: {str(e)}")
            return jsonify({'error': 'Invalid date or time format'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get vehicle_type_id
            cursor.execute("SELECT vehicle_type_id FROM vehicle_types WHERE type_name = %s", (vehicle_type,))
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Invalid vehicle type'}), 400
            vehicle_type_id = result[0]
            
            # Insert booking
            cursor.execute("""
                INSERT INTO bookings (
                    user_id, pickup_location, destination, 
                    booking_date, booking_time, status, vehicle_type_id
                ) VALUES (%s, %s, %s, %s, %s, 'pending', %s)
            """, (
                session['user_id'],
                pickup_location,
                destination,
                booking_date,
                booking_time,
                vehicle_type_id
            ))
            
            booking_id = cursor.lastrowid
            conn.commit()
            
            return jsonify({
                'message': 'Booking created successfully',
                'booking_id': booking_id
            })
            
        except Exception as e:
            print(f"Database error: {str(e)}")
            conn.rollback()
            return jsonify({'error': 'Failed to create booking in database'}), 500
            
    except Exception as e:
        print(f"Error creating booking: {str(e)}")
        return jsonify({'error': 'Failed to create booking'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@bp.route('/bookings/<int:booking_id>', methods=['PUT'])
@user_required
def update_booking(booking_id):
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if booking exists and belongs to user
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE booking_id = %s AND user_id = %s
        """, (booking_id, session['user_id']))
        
        if not cursor.fetchone():
            return jsonify({'error': 'Booking not found'}), 404
        
        # Update booking
        update_fields = []
        update_values = []
        
        if 'pickup_location' in data:
            update_fields.append("pickup_location = %s")
            update_values.append(data['pickup_location'])
        
        if 'destination' in data:
            update_fields.append("dropoff_location = %s")
            update_values.append(data['destination'])
        
        if 'date' in data:
            try:
                booking_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                update_fields.append("booking_date = %s")
                update_values.append(booking_date)
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        if 'time' in data:
            try:
                booking_time = datetime.strptime(data['time'], '%H:%M').time()
                update_fields.append("booking_time = %s")
                update_values.append(booking_time)
            except ValueError:
                return jsonify({'error': 'Invalid time format'}), 400
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        # Add booking_id to values
        update_values.append(booking_id)
        
        # Build and execute update query
        update_query = f"""
            UPDATE bookings 
            SET {', '.join(update_fields)}
            WHERE booking_id = %s
        """
        
        cursor.execute(update_query, update_values)
        conn.commit()
        
        return jsonify({'message': 'Booking updated successfully'})
        
    except Exception as e:
        print(f"Error updating booking: {str(e)}")
        return jsonify({'error': 'Failed to update booking'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@bp.route('/bookings/<int:booking_id>', methods=['DELETE'])
@user_required
def cancel_booking(booking_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if booking exists and belongs to user
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE booking_id = %s AND user_id = %s
        """, (booking_id, session['user_id']))
        
        if not cursor.fetchone():
            return jsonify({'error': 'Booking not found'}), 404
        
        # Update booking status to cancelled
        cursor.execute("""
            UPDATE bookings 
            SET status = 'cancelled'
            WHERE booking_id = %s
        """, (booking_id,))
        
        conn.commit()
        return jsonify({'message': 'Booking cancelled successfully'})
        
    except Exception as e:
        print(f"Error cancelling booking: {str(e)}")
        return jsonify({'error': 'Failed to cancel booking'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close() 