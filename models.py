# from mongoengine import Document, StringField, ReferenceField, DateField, DateTimeField, BooleanField, FloatField, IntField
# from flask_login import UserMixin

# # Note: We don't use 'db.' prefix anymore.

# class User(UserMixin, Document):
#     username = StringField(required=False)  # Username for employees
#     email = StringField(unique=True, required=True)
#     password = StringField(required=True)
#     role = StringField(required=True)  # 'admin' or 'employee'
    
#     # Flask-Login needs a get_id method that returns a string
#     def get_id(self):
#         return str(self.id)

# class Shift(Document):
#     user = ReferenceField(User, required=True)
#     day_of_week = IntField()  # 0=Monday, 1=Tuesday, ..., 6=Sunday (optional for backward compatibility)
#     date = DateField()  # Old field, kept for backward compatibility (will be ignored)
#     start_time = StringField(required=True)
#     end_time = StringField(required=True)
    
#     meta = {
#         'strict': False  # Allow unknown fields for backward compatibility
#     }
    
#     def clean(self):
#         """Ensure day_of_week is set if date exists (migration helper)"""
#         if hasattr(self, 'date') and self.date and not self.day_of_week:
#             # Convert old date to day_of_week (0=Monday, 6=Sunday)
#             self.day_of_week = self.date.weekday()

# class Attendance(Document):
#     user = ReferenceField(User, required=True)
#     check_in_time = DateTimeField()
#     check_out_time = DateTimeField()
#     check_in_latitude = FloatField()
#     check_in_longitude = FloatField()
#     check_out_latitude = FloatField()
#     check_out_longitude = FloatField()
#     photo_filename = StringField()
#     check_in_photo = StringField()  # Add this line to store base64 image data
#     is_late = BooleanField(default=False)
#     admin_approved = BooleanField(default=True)
#     admin_rejected = BooleanField(default=False)  # Track if late entry was rejected
#     late_reason = StringField()  # Reason for lateness