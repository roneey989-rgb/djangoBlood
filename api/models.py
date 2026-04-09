

from django.db import models
from django.contrib.auth.hashers import make_password
import uuid

#User
class User(models.Model):
    ROLE_CHOICES = (
        ('donor', 'Donor'),
        ('doctor', 'Doctor'),
        ('hospital', 'Hospital'),
        ('admin', 'Admin'),
    )

    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=255, null=True, blank=True)

   
    fcm_token = models.TextField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def generate_token(self):
        self.token = str(uuid.uuid4())
        self.save()

    def __str__(self):
        return self.name

#Class Doner  
class Donor(models.Model):
    donor_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    original_name = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=5)
    address = models.CharField(max_length=255,default="Not Provude")  

    def __str__(self):
        return self.original_name




# DOCTOR

class Doctor(models.Model):
    doctor_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    doctor_name = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=5)
    reg_number = models.CharField(max_length=100)
    certificate_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.doctor_name


#  HOSPITAL 

class Hospital(models.Model):
    hospital_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    reg_number = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    certificate_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


#  APPOINTMENT 

class Appointment(models.Model):
    appointment_id = models.AutoField(primary_key=True)
    appointment_code = models.CharField(max_length=20, unique=True)

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, null=True, blank=True, on_delete=models.SET_NULL)
    hospital = models.ForeignKey(Hospital, null=True, blank=True, on_delete=models.SET_NULL)

    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('doctor_approved', 'Doctor Approved'),
            ('completed', 'Completed'),
            ('rejected', 'Rejected'),
        ),
        default='pending'
    )

    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


#  BLOOD PACKET 

class BloodPacket(models.Model):
    packet_id = models.AutoField(primary_key=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)

    blood_group = models.CharField(max_length=5)
    collection_date = models.DateField()
    expiry_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=(
            ('available', 'Available'),
            ('used', 'Used'),
            ('expired', 'Expired'),
        ),
        default='available'
    )


#  BLOOD USAGE

class BloodUsage(models.Model):
    usage_id = models.AutoField(primary_key=True)
    packet = models.ForeignKey(BloodPacket, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)

    patient_name = models.CharField(max_length=100)
    used_date = models.DateField()


# BLOOD REQUEST

class BloodRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    blood_group = models.CharField(max_length=5)
    address = models.CharField(max_length=255)
    
    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('rejected', 'Rejected'),
        ),
        null=True,
        blank=True,
        default='pending'  # automatically set new requests to pending
    )

    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.blood_group} request by {self.user.name} at {self.address}"

# -------------------Doctor varification-------------------
class DoctorVerification(models.Model):
    id = models.AutoField(primary_key=True)

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=10,
        choices=(
            ('fit', 'Fit'),
            ('not_fit', 'Not Fit'),
        )
    )

    remarks = models.TextField(null=True, blank=True)

    verified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.appointment.appointment_id} - {self.status}"
    

#------------------------------NOTIFICATION-----------------------------
class NotificationUser(models.Model):
    notification_id = models.AutoField(primary_key=True)  # primary key
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)  # link to user, nullable

    title = models.CharField(max_length=100)
    message = models.TextField()

    type = models.CharField(max_length=50, default="system")
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title