from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import *
from datetime import timedelta
import uuid
from django.utils import timezone
from .serializers import *
from datetime import date, timedelta
from .ai.health_ai import get_health_ai_response

# SERVER STATUS
@api_view(['GET'])
def serv_status(request):
    return Response({"status": "Server is running"})


# -----------------------SIGNUP---------------------
@api_view(['POST'])
def signup(request):
    try:
        name = request.data.get('name')
        phone = request.data.get('phone')
        password = request.data.get('password')

        if not name or not phone or not password:
            return Response({"error": "All fields required"}, status=400)

        if User.objects.filter(name=name).exists():
            return Response({"error": "Name already taken"}, status=400)

        if User.objects.filter(phone=phone).exists():
            return Response({"error": "Phone already registered"}, status=400)

        user = User(name=name, phone=phone)
        user.set_password(password)
        user.save()

        user.generate_token()
        return Response({
            "message": "Signup successful",
            "token": user.token,
            "user_id": user.user_id,
            "name": user.name,
            "phone": user.phone
            }, status=200)

    except Exception as e:
        return Response({"error": "Server error"}, status=500)


# LOGIN
@api_view(['POST'])
def login(request):
    try:
        phone = request.data.get('phone')
        password = request.data.get('password')

        if not phone or not password:
            return Response({"error": "Phone and password required"}, status=400)

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if not check_password(password, user.password):
            return Response({"error": "Incorrect password"}, status=400)

        if not user.token:
            user.generate_token()
        return Response({
            "message": "Signup successful",
            "token": user.token,
            "user_id": user.user_id,
            "name": user.name,
            "phone": user.phone
            }, status=200)

    except Exception as e:
        return Response({"error": "Server error"}, status=500)


# SET ROLE
@api_view(['POST'])
def set_role(request):
    user_id = request.data.get('user_id')
    role = request.data.get('role')

    VALID_ROLES = ['donor', 'doctor', 'hospital', 'admin']

    if role not in VALID_ROLES:
        return Response({"error": "Invalid role"}, status=400)

    try:
        user = User.objects.get(user_id=user_id)
        user.role = role
        user.save()
        return Response({
            "message": "Role updated",
            "role": user.role
            }, status=200)

      

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


# --------------------------CREATE DONOR-------------------------------
@api_view(['POST'])
def create_donor(request):
    user_id = request.data.get('user_id')
    original_name = request.data.get('original_name')
    blood_group = request.data.get('blood_group')
    address = request.data.get('address')   

    if not user_id or not original_name or not blood_group or not address:
        return Response({"error": "All fields required"}, status=400)

    try:
        user = User.objects.get(user_id=user_id)

        if user.role != "donor":
            return Response({"error": "User is not a donor"}, status=400)

        if Donor.objects.filter(user=user).exists():
            return Response({"error": "Donor already exists"}, status=400)

        donor = Donor.objects.create(
            user=user,
            original_name=original_name,
            blood_group=blood_group,
            address=address   
        )

        return Response({
            "message": "Donor created",
            "donor_id": donor.donor_id
        }, status=200)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


#appoinment

@api_view(['POST'])
def create_appointment(request):
    user_id = request.data.get('user_id')

    try:
        donor = Donor.objects.get(user__user_id=user_id)

        code = str(uuid.uuid4())[:8]

        appointment = Appointment.objects.create(
            donor=donor,
            appointment_code=code,
            status="pending",
            expires_at=timezone.now() + timedelta(days=100)
        )

        return Response({
            "message": "Appointment created",
            "appointment_code": code
        })

    except Donor.DoesNotExist:
        return Response({"error": "Donor not found"}, status=404)
    

#search doner
@api_view(['POST'])
def search_blood(request):
    blood_group = request.data.get('blood_group')
    district = request.data.get('district')

    packets = BloodPacket.objects.filter(
        blood_group=blood_group,
        status="available",
        hospital__address__icontains=district
    )

    hospital_map = {}

    for p in packets:
        h_id = p.hospital.hospital_id

        if h_id not in hospital_map:
            hospital_map[h_id] = {
                "hospital_id": h_id,
                "hospital_name": p.hospital.name,
                "address": p.hospital.address,
                "packet_count": 0
            }

        hospital_map[h_id]["packet_count"] += 1

    return Response(list(hospital_map.values()))

#-----Create doctor entry----------------
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User, Doctor

@api_view(['POST'])
def create_doctor(request):
    user_id = request.data.get('user_id')
    name = request.data.get('doctor_name')
    blood_group = request.data.get('blood_group')
    reg_number = request.data.get('reg_number')
    certificate_url = request.data.get('certificate_url')

    #  VALIDATION
    if not user_id or not name or not blood_group or not reg_number:
        return Response({"error": "All fields required"}, status=400)

    try:
        user = User.objects.get(user_id=user_id)

        #  Prevent duplicate doctor for same user
        if Doctor.objects.filter(user=user).exists():
            return Response({"error": "Doctor already exists"}, status=400)

        # Prevent duplicate registration number
        if Doctor.objects.filter(reg_number=reg_number).exists():
            return Response({"error": "Registration number already used"}, status=400)

        #  CREATE DOCTOR
        doctor = Doctor.objects.create(
            user=user,
            doctor_name=name,
            blood_group=blood_group,
            reg_number=reg_number,
            certificate_url=certificate_url
        )

        #  SET ROLE
        user.role = "doctor"
        user.save()

        return Response({
            "message": "Doctor created successfully",
            "doctor_id": doctor.doctor_id
        })

    except User.DoesNotExist:
        print("user dosent exist")
        return Response({"error": "User not found"}, status=404)

    except Exception as e:
        return Response({"error": "Server error"}, status=500)



# ------------- CHECK APPOINTMENT---------------------
@api_view(['POST'])
def check_appointment(request):

    appointment_id = request.data.get('appointment_id')
    appointment_code = request.data.get('appointment_code')

    try:
        appointment = Appointment.objects.get(
            appointment_id=appointment_id,
            appointment_code=appointment_code
        )

        return Response({"message": "OK"})

    except Appointment.DoesNotExist:
        return Response({"error": "Appointment not found"}, status=404)


# -------------- ADD VERIFICATION--------------------
@api_view(['POST'])
def add_verification(request):

    appointment_id = request.data.get('appointment_id')
    doctor_id = request.data.get('doctor_id')
    status = request.data.get('status')
    #remarks = request.data.get('remarks')

    if not appointment_id or not doctor_id or not status:
        return Response({"error": "All fields required"}, status=400)

    try:
        appointment = Appointment.objects.get(appointment_id=appointment_id)
        doctor = Doctor.objects.get(doctor_id=doctor_id)

        # create verification
        DoctorVerification.objects.create(
            appointment=appointment,
            doctor=doctor,
            status=status,
           # remarks=remarks
        )

        #  update appointment status
        if status == "fit":
            appointment.status = "doctor_approved"
        else:
            appointment.status = "rejected"

        appointment.doctor = doctor
        appointment.save()

        return Response({"message": "Verification added"})

    except Appointment.DoesNotExist:
        return Response({"error": "Appointment not found"}, status=404)

    except Doctor.DoesNotExist:
        return Response({"error": "Doctor not found"}, status=404)
    

#-----------------------HOSPITAL reg----------------------------

@api_view(['POST'])
def create_hospital(request):

    user_id = request.data.get('user_id')
    name = request.data.get('name')
    reg_number = request.data.get('reg_number')
    address = request.data.get('address')

    if not user_id or not name or not reg_number or not address:
        return Response({"error": "All fields required"}, status=400)

    try:
        user = User.objects.get(user_id=user_id)

        #  prevent duplicate hospital per user
        if Hospital.objects.filter(user=user).exists():
            return Response({"error": "Hospital already exists"}, status=400)

        # unique registration number
        if Hospital.objects.filter(reg_number=reg_number).exists():
            return Response({"error": "Registration number already used"}, status=400)

        hospital = Hospital.objects.create(
            user=user,
            name=name,
            reg_number=reg_number,
            address=address
        )

        #  set role
        user.role = "hospital"
        user.save()

        return Response({
            "message": "Hospital created successfully",
            "hospital_id": hospital.hospital_id
        })

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    except Exception as e:
        return Response({"error": "Server error"}, status=500)
    

#----------------------check doner--------------------
@api_view(['POST'])
def check_verification(request):

    appointment_id = request.data.get('appointment_id')
    appointment_code = request.data.get('appointment_code')

    try:
        appointment = Appointment.objects.get(
            appointment_id=appointment_id,
            appointment_code=appointment_code
        )

        # check doctor verification
        verification = DoctorVerification.objects.get(
            appointment=appointment,
            status="fit"
        )

        donor_name = appointment.donor.original_name
        doctor_name = verification.doctor.doctor_name
        verified_at = verification.verified_at

        return Response({
            "message": "Doctor Verified",
            "donor_name": donor_name,
            "doctor_name": doctor_name,
            "verified_at": verified_at
        })

    except Appointment.DoesNotExist:
        return Response({"error": "Appointment not found"}, status=404)

    except DoctorVerification.DoesNotExist:
        return Response({"error": "Not verified / Not fit"}, status=400)


# ================== 2. ADD BLOOD PACKET ==================

@api_view(['POST'])
def add_blood_packet(request):

    appointment_id = request.data.get('appointment_id')
    hospital_id = request.data.get('hospital_id')

    try:
        appointment = Appointment.objects.get(appointment_id=appointment_id)
        hospital = Hospital.objects.get(hospital_id=hospital_id)

        donor = appointment.donor

        today = date.today()
        expiry = today + timedelta(days=35)

        BloodPacket.objects.create(
            hospital=hospital,
            donor=donor,
            blood_group=donor.blood_group,
            collection_date=today,
            expiry_date=expiry,
            status="available"
        )

        return Response({"message": "Blood packet added"})

    except Appointment.DoesNotExist:
        return Response({"error": "Appointment not found"}, status=404)

    except Hospital.DoesNotExist:
        return Response({"error": "Hospital not found"}, status=404)


# ================== 3. BLOOD USAGE ==================

@api_view(['POST'])
def add_blood_usage(request):

    packet_id = request.data.get('packet_id')
    hospital_id = request.data.get('hospital_id')
    patient_name = request.data.get('patient_name')

    if not packet_id or not hospital_id or not patient_name:
        return Response({"error": "All fields required"}, status=400)

    try:
        packet = BloodPacket.objects.get(packet_id=packet_id)
        hospital = Hospital.objects.get(hospital_id=hospital_id)

        BloodUsage.objects.create(
            packet=packet,
            hospital=hospital,
            patient_name=patient_name,
            used_date=date.today()
        )

        #  update packet status
        packet.status = "used"
        packet.save()

        return Response({"message": "Blood used successfully"})

    except BloodPacket.DoesNotExist:
        return Response({"error": "Packet not found"}, status=404)

    except Hospital.DoesNotExist:
        return Response({"error": "Hospital not found"}, status=404)
    
# ----------------------Blood stock---------------------


@api_view(['POST'])
def hospital_blood_stock(request):

    hospital_id = request.data.get('hospital_id')

    packets = BloodPacket.objects.filter(hospital__hospital_id=hospital_id)

    data = []

    for p in packets:
        data.append({
            "packet_id": p.packet_id,
            "donor_id": p.donor.donor_id,
            "donor_name": p.donor.original_name,
            "blood_group": p.blood_group,
            "collection_date": str(p.collection_date),
            "expiry_date": str(p.expiry_date),
            "status": p.status
        })

    return Response(data)


# -------------------------------- 2. BLOOD USAGE TABLE --------------

@api_view(['POST'])
def hospital_usage_table(request):

    hospital_id = request.data.get('hospital_id')

    usage = BloodUsage.objects.filter(hospital__hospital_id=hospital_id)

    data = []

    for u in usage:
        data.append({
            "packet_id": u.packet.packet_id,
            "patient_name": u.patient_name,
            "used_date": str(u.used_date)
        })

    return Response(data)


# -------------------- 3. FIND BLOOD ------------------------

@api_view(['POST'])
def hospital_find_blood(request):

    hospital_id = request.data.get('hospital_id')
    blood_group = request.data.get('blood_group')

    packets = BloodPacket.objects.filter(
        hospital__hospital_id=hospital_id,
        blood_group=blood_group
    )

    data = []

    for p in packets:
        data.append({
            "packet_id": p.packet_id,
            "donor_name": p.donor.original_name,
            "blood_group": p.blood_group,
            "collection_date": str(p.collection_date),
            "expiry_date": str(p.expiry_date),
            "status": p.status
        })

    return Response(data)

#---------------------------AI healht tips---------------------------------
@api_view(['POST'])
def ai_health(request):

    message = request.data.get("message")

    if not message:
        return Response({"error": "Message required"}, status=400)

    reply = get_health_ai_response(message)

    return Response({
        "reply": reply
    })

#-----------------------------request--------------------------------------
@api_view(['POST'])
def create_request(request):
    user_id = request.data.get("user_id")
    blood = request.data.get("blood_group")
    location = request.data.get("location")

    # Get requester name (from user_id)
    user = User.objects.get(user_id=user_id)  # fixed field
    requester_name = user.name

    # Create message
    message_text = f"{blood} blood is required near {location} by {requester_name}"

    # Save request
    req = BloodRequest.objects.create(
        user=user,  # ForeignKey to User
        blood_group=blood,
        address=location,  # updated field name
        status="pending",
        message=message_text
    )

    # Find donors with matching blood group and address
    donors = Donor.objects.filter(
        blood_group=blood,
        address=location  # Donor uses `address`
    )

    # Create notification for each donor
    for d in donors:
        NotificationUser.objects.create(
            user=d.user,  # ForeignKey to User
            title="Blood Request",
            message=message_text,
            type="emergency"
        )

    return Response({"message": "Request created"})

#-------------------------NOTIFICATION-----------------------
@api_view(['POST'])
def get_notifications(request):
    user_id = request.data.get("user_id")

    data = NotificationUser.objects.filter(user_id=user_id).values()

    return Response(list(data))