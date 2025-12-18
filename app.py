# from mongoengine.errors import ValidationError
# import os
# import base64
# import pandas as pd
# from datetime import datetime
# from io import BytesIO
# from flask import Flask, render_template, redirect, url_for, request, flash, send_file
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import LoginManager, login_user, login_required, logout_user, current_user
# from mongoengine import connect
# from models import User, Shift, Attendance

# # --- NEW EMAIL IMPORTS ---
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from email.mime.image import MIMEImage

# # Try to load environment variables from .env file (optional)
# try:
#     from dotenv import load_dotenv
#     load_dotenv()
# except ImportError:
#     pass  # python-dotenv not installed, use environment variables directly

# app = Flask(__name__)
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
# app.config['UPLOAD_FOLDER'] = 'static/uploads'

# # --- EMAIL CONFIGURATION ---
# SMTP_SERVER = 'smtp.gmail.com'
# SMTP_PORT = 587 # Port for TLS
# MAIL_USERNAME = os.environ.get('MAIL_USERNAME') # Sender's email
# MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') # Sender's 16-digit App Password
# ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') # Admin recipient

# # --- MONGODB CONNECTION ---
# # Support both MongoDB Atlas (cloud) and local MongoDB
# MONGODB_URI = os.environ.get('MONGODB_URI')
# if MONGODB_URI:
#     # MongoDB Atlas connection (cloud)
#     print("Connecting to MongoDB Atlas...")
#     connect(host=MONGODB_URI)
# else:
#     # Local MongoDB connection (fallback)
#     print("Connecting to local MongoDB...")
#     connect(db='staff_scheduler', host='localhost', port=27017)

# login_manager = LoginManager()
# login_manager.login_view = 'login'
# login_manager.init_app(app)

# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# @login_manager.user_loader
# def load_user(user_id):
#     try:
#         return User.objects(pk=user_id).first()
#     except ValidationError:
#         # If the ID is invalid (like the old '1'), return None to logout the user
#         return None

# # --- NEW: EMAIL UTILITY FUNCTION ---
# def send_notification_email(subject, body, image_data=None, image_filename='location_photo.png'):
#     if not (MAIL_USERNAME and MAIL_PASSWORD and ADMIN_EMAIL):
#         print("EMAIL CONFIGURATION MISSING: Skipping email notification. Check MAIL_USERNAME, MAIL_PASSWORD, and ADMIN_EMAIL environment variables.")
#         return False

#     try:
#         msg = MIMEMultipart()
#         msg['From'] = MAIL_USERNAME
#         msg['To'] = ADMIN_EMAIL
#         msg['Subject'] = subject
        
#         # Attach the body text
#         msg.attach(MIMEText(body, 'plain'))
        
#         # Attach image if provided
#         if image_data:
#             try:
#                 # Decode base64 image data
#                 header, encoded = image_data.split(",", 1)
#                 image_bytes = base64.b64decode(encoded)
                
#                 # Create image attachment
#                 image_attachment = MIMEImage(image_bytes)
#                 image_attachment.add_header('Content-Disposition', f'attachment; filename={image_filename}')
#                 msg.attach(image_attachment)
#             except Exception as e:
#                 print(f"Warning: Could not attach image to email: {e}")

#         # Connect to the SMTP server
#         with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#             server.starttls()  # Upgrade connection to secure TLS
#             server.login(MAIL_USERNAME, MAIL_PASSWORD)
#             server.sendmail(MAIL_USERNAME, ADMIN_EMAIL, msg.as_string())
        
#         print(f"Email sent successfully to {ADMIN_EMAIL}: {subject}")
#         return True
#     except smtplib.SMTPAuthenticationError:
#         print("Error sending email: SMTP Authentication Failed. Check MAIL_PASSWORD (App Password).")
#         return False
#     except Exception as e:
#         print(f"Error sending email: {e}")
#         return False


# # --- Routes ---

# @app.route('/')
# def index():
#     return redirect(url_for('login'))

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form.get('email')
#         password = request.form.get('password')
        
#         user = User.objects(email=email).first()
        
#         if user and check_password_hash(user.password, password):
#             login_user(user)
#             return redirect(url_for('admin_dashboard' if user.role == 'admin' else 'employee_dashboard'))
#         flash('Invalid credentials')
#     return render_template('login.html')

# @app.route('/employee', methods=['GET', 'POST'])
# @login_required
# def employee_dashboard():
#     # Get shifts and migrate old ones if needed
#     my_shifts = []
#     try:
#         for shift in Shift.objects(user=current_user):
#             try:
#                 # Migrate old shifts that have date but no day_of_week
#                 if hasattr(shift, 'date') and shift.date and not shift.day_of_week:
#                     shift.day_of_week = shift.date.weekday()
#                     shift.save()
#                 # Only include shifts with day_of_week set
#                 if shift.day_of_week is not None:
#                     my_shifts.append(shift)
#             except Exception as e:
#                 # Skip problematic shifts
#                 print(f"Error processing shift {shift.id}: {e}")
#                 continue
#     except Exception as e:
#         flash('Some shifts could not be loaded. Please contact admin.')
#         print(f"Error loading shifts: {e}")
    
#     # Sort by day of week (0=Monday, 6=Sunday)
#     my_shifts.sort(key=lambda x: x.day_of_week if x.day_of_week is not None else 999)
#     current_session = Attendance.objects(user=current_user, check_out_time=None).first()
    
#     return render_template('employee.html', shifts=my_shifts, current_session=current_session)

# @app.route('/checkin', methods=['POST'])
# @login_required
# def check_in():
#     image_data = request.form.get('image')
#     latitude = request.form.get('lat')
#     longitude = request.form.get('lng')
#     late_reason = request.form.get('late_reason', '').strip()
    
#     if not image_data:
#         flash('Camera photo mandatory!')
#         return redirect(url_for('employee_dashboard'))

#     try:
#         header, encoded = image_data.split(",", 1)
#         base64.b64decode(encoded)
#     except Exception as e:
#         flash(f'Error processing photo: {e}')
#         return redirect(url_for('employee_dashboard'))

#     now = datetime.now()
#     today_weekday = now.weekday()
#     today_shift = Shift.objects(user=current_user, day_of_week=today_weekday).first()
    
#     if not today_shift:
#         flash('You do not have a shift assigned for today. Please contact admin.')
#         return redirect(url_for('employee_dashboard'))
    
#     # Allow check-in at any time on the day of the shift (before, during, or after shift start)
#     is_late = False
#     requires_approval = True
#     check_in_status = "ON TIME"
    
#     shift_start = datetime.strptime(today_shift.start_time, "%H:%M").time()
#     current_time = now.time()
    
#     # Compare times to determine if late (only mark as late if current time is after shift start)
#     if current_time > shift_start:
#         is_late = True
#         requires_approval = False
#         check_in_status = "LATE"
#         if not late_reason:
#             flash('Please provide a reason for lateness!')
#             return redirect(url_for('employee_dashboard'))
#         flash('You are late! Admin approval requested.')
#     elif current_time < shift_start:
#         # Employee is checking in early (before shift start) - this is allowed
#         check_in_status = "EARLY"
#         flash('Checked in early. Great job!')

#     attendance = Attendance(
#         user=current_user,
#         check_in_time=now,
#         check_in_latitude=float(latitude) if latitude else None,
#         check_in_longitude=float(longitude) if longitude else None,
#         check_in_photo=image_data,
#         photo_filename=None,
#         is_late=is_late,
#         admin_approved=requires_approval,
#         late_reason=late_reason if is_late else None
#     )
#     attendance.save()

#     # --- NEW: SEND CHECK-IN EMAIL ---
#     username_display = current_user.username if current_user.username else current_user.email
#     subject = f"ATTENDANCE CHECK-IN: {username_display} - {check_in_status}"
    
#     body = f"""
# Dear Admin,

# Employee {username_display} ({current_user.email}) has checked in.

# Check-in Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
# Shift Start: {today_shift.start_time}
# Status: {check_in_status}
# Location: Lat {latitude}, Lng {longitude}
# """
    
#     if is_late:
#         body += f"""
# Reason for Lateness: {late_reason}
# Approval Status: Pending Approval

# Please review and approve or reject this late entry in the admin dashboard.
# """
#     else:
#         body += "\nThis is an automated notification."
    
#     # Send email with image attachment
#     send_notification_email(subject, body, image_data=image_data)
#     # --- END EMAIL ---
    
#     flash('Checked in successfully!')
#     return redirect(url_for('employee_dashboard'))

# @app.route('/checkout', methods=['POST'])
# @login_required
# def check_out():
#     latitude = request.form.get('lat')
#     longitude = request.form.get('lng')
    
#     attendance = Attendance.objects(user=current_user, check_out_time=None).first()
#     if attendance:
#         now = datetime.now()
#         attendance.check_out_time = now
#         attendance.check_out_latitude = float(latitude) if latitude else None
#         attendance.check_out_longitude = float(longitude) if longitude else None
#         attendance.save()

#         # --- NEW: SEND CHECK-OUT EMAIL ---
#         duration = 'N/A'
#         if attendance.check_in_time:
#             delta = now - attendance.check_in_time
#             hours = int(delta.total_seconds() // 3600)
#             minutes = int((delta.total_seconds() % 3600) // 60)
#             duration = f"{hours}h {minutes}m"

#         username_display = current_user.username if current_user.username else current_user.email
#         subject = f"ATTENDANCE CHECK-OUT: {username_display}"
#         body = f"""
# Dear Admin,

# Employee {username_display} ({current_user.email}) has checked out.

# Check-in Time: {attendance.check_in_time.strftime('%Y-%m-%d %H:%M:%S')}
# Check-out Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
# Total Duration: {duration}

# Check-out Location: Lat {latitude}, Lng {longitude}

# This is an automated notification.
# """
#         send_notification_email(subject, body)
#         # --- END EMAIL ---

#         flash('Checked out successfully!')
#     else:
#         flash('No active check-in session found.')
#     return redirect(url_for('employee_dashboard'))

# @app.route('/admin', methods=['GET', 'POST'])
# @login_required
# def admin_dashboard():
#     if current_user.role != 'admin':
#         return redirect(url_for('login'))
        
#     if request.method == 'POST':
#         if 'create_email' in request.form:
#             new_username = request.form.get('create_username')
#             new_email = request.form.get('create_email')
#             new_pass = request.form.get('create_password')
            
#             if User.objects(email=new_email).first():
#                 flash('Email already exists!')
#             else:
#                 User(
#                     username=new_username,
#                     email=new_email, 
#                     password=generate_password_hash(new_pass), 
#                     role='employee'
#                 ).save()
#                 flash('Employee created!')

#         elif 'user_id' in request.form:
#             user_id = request.form.get('user_id')
#             user_obj = User.objects(pk=user_id).first()
#             days = request.form.getlist('days')  # Get all selected days
#             start = request.form.get('start')
#             end = request.form.get('end')
            
#             if not days:
#                 flash('Please select at least one day!', 'error')
#             else:
#                 created_count = 0
#                 updated_count = 0
                
#                 for day_str in days:
#                     day_of_week = int(day_str)
#                     # Check if shift already exists for this day
#                     existing = Shift.objects(user=user_obj, day_of_week=day_of_week).first()
#                     if existing:
#                         existing.start_time = start
#                         existing.end_time = end
#                         existing.save()
#                         updated_count += 1
#                     else:
#                         Shift(
#                             user=user_obj,
#                             day_of_week=day_of_week,
#                             start_time=start,
#                             end_time=end
#                         ).save()
#                         created_count += 1
                
#                 if created_count > 0 and updated_count > 0:
#                     flash(f'Shifts allocated: {created_count} created, {updated_count} updated.')
#                 elif created_count > 0:
#                     flash(f'{created_count} shift(s) allocated successfully!')
#                 elif updated_count > 0:
#                     flash(f'{updated_count} shift(s) updated successfully!')
        
#         elif 'delete_shift_id' in request.form:
#             shift_id = request.form.get('delete_shift_id')
#             shift = Shift.objects(pk=shift_id).first()
#             if shift:
#                 shift.delete()
#                 flash('Shift deleted.')

#     employees = User.objects(role='employee')
#     attendances = Attendance.objects().order_by('-check_in_time')
    
#     # Organize shifts by employee for display
#     all_shifts = []
#     try:
#         for shift in Shift.objects():
#             try:
#                 # Migrate old shifts that have date but no day_of_week
#                 if hasattr(shift, 'date') and shift.date and not shift.day_of_week:
#                     shift.day_of_week = shift.date.weekday()
#                     shift.save()
#                 if shift.day_of_week is not None:
#                     all_shifts.append(shift)
#             except Exception as e:
#                 print(f"Error processing shift: {e}")
#                 continue
#     except Exception as e:
#         print(f"Error loading shifts: {e}")
    
#     shifts_by_employee = {}
#     for shift in all_shifts:
#         emp_id = str(shift.user.id)
#         if emp_id not in shifts_by_employee:
#             shifts_by_employee[emp_id] = []
#         shifts_by_employee[emp_id].append(shift)
    
#     # Sort shifts by day of week for each employee
#     for emp_id in shifts_by_employee:
#         shifts_by_employee[emp_id].sort(key=lambda x: x.day_of_week if x.day_of_week is not None else 999)

#     return render_template('admin.html', employees=employees, attendances=attendances, shifts_by_employee=shifts_by_employee)

# @app.route('/approve_attendance/<attendance_id>', methods=['POST'])
# @login_required
# def approve_attendance(attendance_id):
#     if current_user.role != 'admin':
#         return redirect(url_for('login'))
    
#     attendance = Attendance.objects(pk=attendance_id).first()
#     if attendance and attendance.is_late:
#         attendance.admin_approved = True
#         attendance.admin_rejected = False
#         attendance.save()
        
#         # Send approval email
#         subject = f"LATE ENTRY APPROVED: {attendance.user.email}"
#         body = f"""
# Dear Admin,

# You have APPROVED the late entry for employee {attendance.user.email}.

# Check-in Time: {attendance.check_in_time.strftime('%Y-%m-%d %H:%M:%S')}
# Reason for Lateness: {attendance.late_reason or 'Not provided'}
# Status: APPROVED

# This is an automated notification.
# """
#         send_notification_email(subject, body, image_data=attendance.check_in_photo)
        
#         flash('Late entry approved successfully!')
#     else:
#         flash('Attendance record not found or not a late entry.')
    
#     return redirect(url_for('admin_dashboard'))

# @app.route('/reject_attendance/<attendance_id>', methods=['POST'])
# @login_required
# def reject_attendance(attendance_id):
#     if current_user.role != 'admin':
#         return redirect(url_for('login'))
    
#     attendance = Attendance.objects(pk=attendance_id).first()
#     if attendance and attendance.is_late:
#         attendance.admin_approved = False
#         attendance.admin_rejected = True
#         attendance.save()
        
#         # Send rejection email
#         subject = f"LATE ENTRY REJECTED: {attendance.user.email}"
#         body = f"""
# Dear Admin,

# You have REJECTED the late entry for employee {attendance.user.email}.

# Check-in Time: {attendance.check_in_time.strftime('%Y-%m-%d %H:%M:%S')}
# Reason for Lateness: {attendance.late_reason or 'Not provided'}
# Status: REJECTED

# This is an automated notification.
# """
#         send_notification_email(subject, body, image_data=attendance.check_in_photo)
        
#         flash('Late entry rejected.')
#     else:
#         flash('Attendance record not found or not a late entry.')
    
#     return redirect(url_for('admin_dashboard'))

# @app.route('/export')
# @login_required
# def export_data():
#     if current_user.role != 'admin':
#         return "Unauthorized"
        
#     attendances = Attendance.objects().order_by('-check_in_time')
#     data = []
    
#     for att in attendances:
#         check_in = att.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if att.check_in_time else 'N/A'
#         check_out = att.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if att.check_out_time else 'N/A'
        
#         # Calculate duration if checked out
#         duration = 'N/A'
#         if att.check_in_time and att.check_out_time:
#             delta = att.check_out_time - att.check_in_time
#             hours = int(delta.total_seconds() // 3600)
#             minutes = int((delta.total_seconds() % 3600) // 60)
#             duration = f"{hours}h {minutes}m"
        
#         status = "Late" if att.is_late else "On Time"
#         if att.is_late:
#             if att.admin_rejected:
#                 approval_status = "Rejected"
#             elif att.admin_approved:
#                 approval_status = "Approved"
#             else:
#                 approval_status = "Pending Approval"
#         else:
#             approval_status = "N/A"
        
#         check_in_location = f"{att.check_in_latitude:.6f}, {att.check_in_longitude:.6f}" if (att.check_in_latitude is not None and att.check_in_longitude is not None) else 'N/A'
#         check_out_location = f"{att.check_out_latitude:.6f}, {att.check_out_longitude:.6f}" if (att.check_out_latitude is not None and att.check_out_longitude is not None) else 'N/A'
        
#         employee_display = f"{att.user.username} ({att.user.email})" if att.user.username else att.user.email
        
#         data.append({
#             'Employee': employee_display,
#             'Check In': check_in,
#             'Check In Location': check_in_location,
#             'Check Out': check_out,
#             'Check Out Location': check_out_location,
#             'Duration': duration,
#             'Status': status,
#             'Reason for Lateness': att.late_reason if att.is_late and att.late_reason else 'N/A',
#             'Approval Status': approval_status if approval_status else 'N/A'
#         })
    
#     df = pd.DataFrame(data)
#     output = BytesIO()
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         df.to_excel(writer, index=False, sheet_name='Attendance')
        
#         # Get the workbook and worksheet to adjust column widths
#         workbook = writer.book
#         worksheet = writer.sheets['Attendance']
        
#         # Auto-adjust column widths
#         for idx, col in enumerate(df.columns):
#             max_length = max(
#                 df[col].astype(str).apply(len).max(),
#                 len(col)
#             ) + 2
#             worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
#     output.seek(0)
#     return send_file(output, download_name="attendance_report.xlsx", as_attachment=True)

# @app.route('/migrate-shifts')
# @login_required
# def migrate_shifts():
#     """Migrate old shifts from date-based to day_of_week-based using direct MongoDB access"""
#     if current_user.role != 'admin':
#         return "Unauthorized"
    
#     migrated = 0
#     deleted = 0
    
#     try:
#         # Get MongoDB connection directly
#         from mongoengine import get_db
#         db = get_db()
#         shift_collection = db['shift']
        
#         all_shifts = list(shift_collection.find())
        
#         for shift_doc in all_shifts:
#             try:
#                 if 'date' in shift_doc and shift_doc['date'] and 'day_of_week' not in shift_doc:
#                     from datetime import datetime as dt
#                     if isinstance(shift_doc['date'], str):
#                         date_obj = dt.strptime(shift_doc['date'], '%Y-%m-%d').date()
#                     else:
#                         date_obj = shift_doc['date']
#                     day_of_week = date_obj.weekday()
#                     shift_collection.update_one(
#                         {'_id': shift_doc['_id']},
#                         {'$set': {'day_of_week': day_of_week}}
#                     )
#                     migrated += 1
#                 elif 'day_of_week' not in shift_doc and ('date' not in shift_doc or not shift_doc.get('date')):
#                     shift_collection.delete_one({'_id': shift_doc['_id']})
#                     deleted += 1
#             except Exception as e:
#                 try:
#                     shift_collection.delete_one({'_id': shift_doc['_id']})
#                     deleted += 1
#                 except:
#                     pass
        
#     except Exception as e:
#         return f"Migration error: {str(e)}. <a href='/admin'>Back to Admin</a>"
    
#     return f"Migration complete. Migrated: {migrated}, Deleted: {deleted}. <a href='/admin'>Back to Admin</a>"

# @app.route('/logo')
# def serve_logo():
#     """Serve the organization logo"""
#     import os
#     logo_paths = [
#         'static/uploads/logo.jpeg',
#         'static/uploads/logo.jpg',
#         'static/uploads/logo.png',
#         'static/logo.png',
#         'static/logo.jpeg',
#         'static/images/logo.png'
#     ]
    
#     for path in logo_paths:
#         if os.path.exists(path):
#             return send_file(path)
    
#     from flask import Response
#     return Response("Logo not found", status=404)

# @app.route('/logout')
# def logout():
#     logout_user()
#     return redirect(url_for('login'))

# if __name__ == '__main__':
#     # Ensure Admin exists
#     try:
#         if not User.objects(email='admin@company.com').first():
#             User(email='admin@company.com', password=generate_password_hash('admin123'), role='admin').save()
#             print("Admin created: admin@company.com / admin123")
#     except Exception as e:
#         print(f"DB Error (Make sure MongoDB is running): {e}")
        
#     app.run(debug=True)