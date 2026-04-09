from rest_framework import serializers
from .models import *

#user
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'user_id',
            'name',
            'phone',
            'role',
            'created_at'
        ]

#Doner
class DonorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = '__all__'




# DOCTOR
class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'


# HOSPITAL
class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'


# APPOINTMENT
class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'


# BLOOD PACKET
class BloodPacketSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodPacket
        fields = '__all__'


# BLOOD USAGE
class BloodUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodUsage
        fields = '__all__'


# BLOOD REQUEST
class BloodRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodRequest
        fields = '__all__'

#doctor varification
class DoctorVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorVerification
        fields = '__all__'