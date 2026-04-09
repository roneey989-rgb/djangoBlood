from django.contrib import admin
from .models import *

# ---------------- USER ----------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'phone', 'role', 'created_at')
    search_fields = ('name', 'phone')
    list_filter = ('role',)

# ---------------- DONOR ----------------
@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('donor_id', 'original_name', 'blood_group', 'address')
    search_fields = ('original_name', 'blood_group')

# ---------------- DOCTOR ----------------
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('doctor_id', 'doctor_name', 'blood_group', 'reg_number')
    search_fields = ('doctor_name', 'reg_number')

# ---------------- HOSPITAL ----------------
@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('hospital_id', 'name', 'reg_number', 'address')
    search_fields = ('name', 'reg_number')

# ---------------- APPOINTMENT ----------------
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'appointment_code', 'status', 'created_at')
    list_filter = ('status',)

# ---------------- BLOOD PACKET ----------------
@admin.register(BloodPacket)
class BloodPacketAdmin(admin.ModelAdmin):
    list_display = ('packet_id', 'blood_group', 'status', 'collection_date', 'expiry_date')
    list_filter = ('status', 'blood_group')

# ---------------- BLOOD USAGE ----------------
@admin.register(BloodUsage)
class BloodUsageAdmin(admin.ModelAdmin):
    list_display = ('usage_id', 'patient_name', 'used_date')

# ---------------- BLOOD REQUEST ----------------
@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'blood_group', 'status', 'created_at')
    list_filter = ('status',)

# ---------------- DOCTOR VERIFICATION ----------------
@admin.register(DoctorVerification)
class DoctorVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'verified_at')
    list_filter = ('status',)

# ---------------- NOTIFICATION ----------------
@admin.register(NotificationUser)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_id', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('is_read', 'type')