from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import *
from datetime import timedelta
import uuid
from django.utils import timezone
from .serializers import *
from datetime import date, timedelta
from .ai.health_ai import get_health_ai_response
import requests
import random
from twilio.rest import Client

import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
 


from rest_framework.decorators import api_view
from rest_framework.response import Response




# ensure initialized
if not firebase_admin._apps:
    from .firebase import *


    
from django.conf import settings


client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)

verify_sid = settings.TWILIO_VERIFY_SID


AUTH_KEY = "507055AYCumuqGh69de009bP1" #OTP
TEMPLATE_ID = "YOUR_TEMPLATE_ID" #OTP

# SERVER STATUS
@api_view(['GET'])
def serv_status(request):
    return Response({"status": "Server is running"})


# ----------------------- START SIGNUP---------------------
@api_view(['POST'])
def start_signup(request):
    name = request.data.get('name')
    phone = request.data.get('phone')
    password = request.data.get('password')

    if not name or not phone or not password:
        return Response({"error": "All fields required"}, status=400)

    if User.objects.filter(name=name).exists():
        return Response({"error": "Name already taken"}, status=400)

    if User.objects.filter(phone=phone).exists():
        return Response({"error": "Phone already registered"}, status=400)

    #  SEND OTP
    client.verify.services(verify_sid).verifications.create(
        to="+91" + phone,
        channel="sms"
    )

    return Response({
        "message": "OTP sent",
        "mode": "signup",
        "name": name,
        "password": password
    })

#------------------start LOGIN------------------
@api_view(['POST'])
def start_login(request):
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

    #  SEND OTP
    client.verify.services(verify_sid).verifications.create(
        to="+91" + phone,
        channel="sms"
    )

    return Response({"message": "OTP sent", "mode": "login"})

#-----------------------VAEIFY OTP-------------------
@api_view(['POST'])
def verify_otp(request):
    phone = request.data.get('phone')
    otp = request.data.get('otp')
    mode = request.data.get('mode')

    try:
        verification_check = client.verify.services(verify_sid).verification_checks.create(
            to="+91" + phone,
            code=otp
        )
    except Exception as e:
        return Response({"error": "OTP verification failed"}, status=500)

    if verification_check.status != "approved":
        return Response({"error": "Invalid OTP"}, status=400)

    # ---------------- LOGIN ----------------
    if mode == "login":
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        #  GENERATE CUSTOM TOKEN
        user.generate_token()

        return Response({
            "message": "Login successful",
            "user_id": user.user_id,
            "name": user.name,
            "phone": user.phone,
            "token": user.token   # USE YOUR TOKEN
        })

    # ---------------- SIGNUP ----------------
    elif mode == "signup":
        name = request.data.get("name")
        password = request.data.get("password")

        # Prevent duplicate
        if User.objects.filter(phone=phone).exists():
            return Response({"error": "Phone already registered"}, status=400)

        user = User(name=name, phone=phone)
        user.set_password(password)
        user.save()

        # GENERATE TOKEN AFTER CREATE
        user.generate_token()

        return Response({
            "message": "Signup successful",
            "user_id": user.user_id,
            "name": user.name,
            "phone": user.phone,
            "token": user.token   #  USE YOUR TOKEN
        })

    return Response({"error": "Invalid mode"}, status=400)


#----------------------------- SET ROLE------------------------------------------------------------
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

#------------------------------------------- permission classes-----------------------------
@api_view(['GET'])
def get_user_data(request):

    #  GET TOKEN FROM HEADER
    auth_header = request.headers.get("Authorization")
    print("auth header:",auth_header)
    if not auth_header:
        return Response({"error": "No token provided"}, status=401)

    token = auth_header.replace("Bearer ", "")
    print("TOKEN RECIVED:",token)
    #  FIND USER USING TOKEN
    try:
        user = User.objects.get(token=token)
        print("user found:",user)
    except User.DoesNotExist:
        print("user not found for token")
        return Response({"error": "Invalid token"}, status=401)

    #  GET RELATED PROFILES
    donor = Donor.objects.filter(user=user).first()
    doctor = Doctor.objects.filter(user=user).first()
    hospital = Hospital.objects.filter(user=user).first()

    #  RESPONSE (UNCHANGED LOGIC)
    return Response({
        "user_id": user.user_id,
        "name": user.name,
        "phone": user.phone,
        "role": user.role,

        # EXIST CHECK
        "has_donor": donor is not None,
        "has_doctor": doctor is not None,
        "has_hospital": hospital is not None,

        # RETURN IDS
        "donor_id": donor.donor_id if donor else None,
        "doctor_id": doctor.doctor_id if doctor else None,
        "hospital_id": hospital.hospital_id if hospital else None,
    })


#---------------------------------- SAVE TOKEN --------------------------------



@api_view(['POST'])
def save_fcm_token(request):

    #  GET TOKEN FROM HEADER
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return Response({"error": "No token provided"}, status=401)

    token = auth_header.replace("Bearer ", "")

    #  FIND USER
    try:
        user = User.objects.get(token=token)
    except User.DoesNotExist:
        return Response({"error": "Invalid token"}, status=401)

    #  GET FCM TOKEN
    fcm_token = request.data.get("fcm_token")
    print (fcm_token)
    if not fcm_token:
        return Response({"error": "FCM token missing"}, status=400)

    #  SAVE
    user.fcm_token = fcm_token
    user.save()

    return Response({"message": "FCM saved successfully"})
# --------------------------CREATE DONOR-------------------------------
@api_view(['POST'])
def create_donor(request):
    user_id = request.data.get('user_id')
    original_name = request.data.get('original_name')
    blood_group = request.data.get('blood_group')
    address = request.data.get('address')

    #  NEW FIELDS
    state = request.data.get('state')
    district = request.data.get('district')

    if not user_id or not original_name or not blood_group or not address or not state or not district:
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
            address=address,
            state=state,           #  added
            district=district      #  added
        )

        return Response({
            "message": "Donor created",
            "donor_id": donor.donor_id
        }, status=200)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

#------------------------appoinment--------------------------------------------------
from datetime import date, timedelta
from django.utils import timezone
import uuid

@api_view(['POST'])
def create_appointment(request):
    user_id = request.data.get('user_id')

    try:
        donor = Donor.objects.get(user__user_id=user_id)

        # 🔥 CHECK LAST DONATION DATE
        if donor.last_donation_date:
            today = date.today()
            next_allowed_date = donor.last_donation_date + timedelta(days=54)

            if today < next_allowed_date:
                remaining_days = (next_allowed_date - today).days

                return Response({
                    "error": "You cannot donate blood yet you can donate after {remaining_days} days",
                    "next_allowed_date": str(next_allowed_date),
                    "remaining_days": remaining_days
                }, status=400)

        # 🔥 CHECK IF APPOINTMENT ALREADY EXISTS
        existing_appointment = Appointment.objects.filter(
            donor=donor,
            status="pending"
        ).first()

        if existing_appointment:
            return Response({
                "error": "You already have an active appointment",
                "appointment_code": existing_appointment.appointment_code
            }, status=400)

        # 🔥 CREATE NEW APPOINTMENT
        code = str(uuid.uuid4())[:8]

        appointment = Appointment.objects.create(
            donor=donor,
            appointment_code=code,
            status="pending",
            expires_at=timezone.now() + timedelta(days=1)
        )

        return Response({
            "message": "Appointment created",
            "appointment_code": code
        })

    except Donor.DoesNotExist:
        return Response({"error": "Donor not found"}, status=404)

    

#-------------------------------------------search doner-----------------------------------------------------
@api_view(['POST'])
def search_blood(request):
    blood_group = request.data.get('blood_group')
    district = request.data.get('district')
    print(district)
    packets = BloodPacket.objects.filter(
        blood_group=blood_group,
        status="available",
        hospital__district__icontains=district
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
    print(list(hospital_map.values()))
    return Response(list(hospital_map.values()))

#-----Create doctor entry----------------
@api_view(['POST'])
def create_doctor(request):
    user_id = request.data.get('user_id')
    name = request.data.get('doctor_name')
    blood_group = request.data.get('blood_group')
    reg_number = request.data.get('reg_number')
    certificate_url = request.data.get('certificate_url')

    # ✅ NEW FIELDS
    state = request.data.get('state')
    district = request.data.get('district')
    address = request.data.get('address')

    # VALIDATION
    if not user_id or not name or not blood_group or not reg_number or not state or not district or not address:
        return Response({"error": "All fields required"}, status=400)

    try:
        user = User.objects.get(user_id=user_id)

        if Doctor.objects.filter(user=user).exists():
            return Response({"error": "Doctor already exists"}, status=400)

        if Doctor.objects.filter(reg_number=reg_number).exists():
            return Response({"error": "Registration number already used"}, status=400)

        # ✅ CREATE DOCTOR (UPDATED)
        doctor = Doctor.objects.create(
            user=user,
            doctor_name=name,
            blood_group=blood_group,
            reg_number=reg_number,
            certificate_url=certificate_url,
            state=state,
            district=district,
            address=address   # ✅ NEW
        )

        user.role = "doctor"
        user.save()

        return Response({
            "message": "Doctor created successfully",
            "doctor_id": doctor.doctor_id
        })

    except User.DoesNotExist:
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
    state = request.data.get('state')
    district = request.data.get('district')

    if not user_id or not name or not reg_number or not address or not state or not district:
        return Response({"error": "All fields required"}, status=400)

    try:
        user = User.objects.get(user_id=user_id)

        if Hospital.objects.filter(user=user).exists():
            return Response({"error": "Hospital already exists"}, status=400)

        if Hospital.objects.filter(reg_number=reg_number).exists():
            return Response({"error": "Registration number already used"}, status=400)

        hospital = Hospital.objects.create(
            user=user,
            name=name,
            reg_number=reg_number,
            address=address,
            state=state,
            district=district
        )

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

        # ALLOW if ANY ONE is approved
        if not (
            appointment.status == "doctor_approved" or
            appointment.status2 == "hospital_approved"
        ):
            return Response(
                {"error": "Approval required (doctor or hospital)"},
                status=400
            )

        donor = appointment.donor

        today = date.today()
        expiry = today + timedelta(days=35)

        # 🔥 CREATE BLOOD PACKET (UNCHANGED)
        BloodPacket.objects.create(
            hospital=hospital,
            donor=donor,
            blood_group=donor.blood_group,
            collection_date=today,
            expiry_date=expiry,
            status="available"
        )

        # 🔥 UPDATE DONOR LAST DONATION DATE (NEW)
        donor.last_donation_date = today
        donor.save()

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

    today = date.today()

    # 🔥 BULK UPDATE (FASTER)
    BloodPacket.objects.filter(
        hospital__hospital_id=hospital_id,
        expiry_date__lt=today
    ).exclude(status="expired").update(status="expired")

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
    district = request.data.get("district")

    user = User.objects.get(user_id=user_id)
    requester_name = user.name

    message_text = f"{blood} blood is required near {location} by {requester_name}"

    req = BloodRequest.objects.create(
        user=user,
        blood_group=blood,
        address=location,
        district=district,
        status="avalable",
        message=message_text
    )

    donors = Donor.objects.filter(
        blood_group=blood,
        district=district
    )

    for d in donors:

        # ✅ existing DB logic
        NotificationUser.objects.create(
            user=d.user,
            title="Blood Request",
            message=message_text,
            type="avalable",
            request_id=req.request_id,
            requester_id=user.user_id
        )

        # 🔥 SEND PUSH (NEW)
        if d.user.fcm_token:
            send_push_notification(
                token=d.user.fcm_token,
                title="🩸 Blood Needed",
                body=message_text,
                data={
                    "request_id": str(req.request_id),
                    "type": "blood_request"
                }
            )

    return Response({"message": "Request created"})
# ------------------ GET NOTIFICATIONS ------------------
@api_view(['POST'])
def get_notifications(request):

    user_id = request.data.get("user_id")

    if not user_id:
        return Response({"error": "User ID required"}, status=400)

    try:
        user_id = int(user_id)
    except:
        return Response({"error": "Invalid user ID"}, status=400)

    data = NotificationUser.objects.filter(user_id=user_id).values()

    return Response(list(data))


# ------------------ ACCEPT REQUEST ------------------
@api_view(['POST'])
def accept_request(request):

    request_id = request.data.get("request_id")
    donor_id = request.data.get("donor_id")

    if not request_id or not donor_id:
        return Response({"error": "Missing data"}, status=400)

    try:
        blood_request = BloodRequest.objects.get(request_id=request_id)
    except BloodRequest.DoesNotExist:
        return Response({"error": "Request not found"}, status=404)

    if blood_request.status == "pending":
        return Response({"message": "Request is already pending"})

    try:
        donor = User.objects.get(user_id=donor_id)
    except User.DoesNotExist:
        return Response({"error": "Donor not found"}, status=404)

    requester = blood_request.user  # 👈 this has phone

    # Prevent duplicate accept
    if RequestAccept.objects.filter(request=blood_request, donor=donor).exists():
        return Response({"message": "Already accepted"})

    # CREATE ACCEPT RECORD
    RequestAccept.objects.create(
        request=blood_request,
        donor=donor,
        requester=requester
    )

    # UPDATE STATUS
    blood_request.status = "pending"
    blood_request.save()

    # NOTIFICATION
    NotificationUser.objects.create(
        user=requester,
        title="Donor Accepted",
        message=f"{donor.name} accepted your request",
        type="DA",
        request_id=blood_request.request_id,
        requester_id=donor.user_id
    )

    NotificationUser.objects.filter(
        request_id=request_id,
        requester_id=requester.user_id
    ).exclude(
        user=requester
    ).update(
        message="This request is now pending",
        type="pending"
    )

    # 🔥 RETURN PHONE NUMBER
    return Response({
        "message": "Accepted successfully",
        "requester_phone": requester.phone
    })

#----------------------------CONFORM REQUEST---------------------------------
@api_view(['POST'])
def confirm_request(request):

    request_id = request.data.get("request_id")

    try:
        blood_request = BloodRequest.objects.get(request_id=request_id)
    except BloodRequest.DoesNotExist:
        return Response({"error": "Request not found"}, status=404)

    # ✅ update blood request
    blood_request.status = "fulfilled"
    blood_request.save()

    # ✅ update accept table
    RequestAccept.objects.filter(request=blood_request).update(status="accepted")

    # ✅ update all notifications
    NotificationUser.objects.filter(
        request_id=request_id
    ).update(
        message="Blood request completed",
        type="completed"
    )

    return Response({"message": "Request completed"})


#------------------------REJECT REQUEST---------------------
@api_view(['POST'])
def reject_request(request):

    request_id = request.data.get("request_id")

    try:
        blood_request = BloodRequest.objects.get(request_id=request_id)
    except BloodRequest.DoesNotExist:
        return Response({"error": "Request not found"}, status=404)

    # ✅ revert status
    blood_request.status = "available"
    blood_request.save()

    # ✅ update accept table
    RequestAccept.objects.filter(request=blood_request).update(status="rejected")

    # ✅ restore original message
    message_text = blood_request.message

    NotificationUser.objects.filter(
        request_id=request_id
    ).update(
        message=message_text,
        type="available"
    )

    return Response({"message": "Request rejected"})

#--------------------------------------Search Doctor Hospital------------------------------
@api_view(['POST'])
def search_doctors_hospitals(request):

    district = request.data.get('district', '').strip()

    if not district:
        return Response({"error": "District required"}, status=400)

    print("SEARCH DISTRICT:", district)

    # ---------------- DOCTORS ----------------
    doctors = Doctor.objects.filter(
        district__iexact=district,
        status="verified"
    )

    # ---------------- HOSPITALS ----------------
    hospitals = Hospital.objects.filter(
        district__iexact=district,
        status="verified"
    )

    print("DOCTORS FOUND:", doctors.count())
    print("HOSPITALS FOUND:", hospitals.count())

    data = []

    # Add doctors
    for d in doctors:
        data.append({
            "type": "doctor",
            "name": d.doctor_name,
            "address": f"{d.address}, {d.district}, {d.state}",
            "extra": f"Blood Group: {d.blood_group}"
        })

    # Add hospitals
    for h in hospitals:
        data.append({
            "type": "hospital",
            "name": h.name,
            "address": f"{h.address}, {h.district}, {h.state}",
            "extra": f"District: {h.district}"
        })

    print("FINAL DATA:", data)

    return Response(data)


#-----------------------------------------verify doner by hospital-------------------------------------
@api_view(['POST'])
def approve_by_hospital(request):

    appointment_id = request.data.get("appointment_id")
    hospital_id = request.data.get("hospital_id")

    if not appointment_id or not hospital_id:
        return Response({"error": "Missing data"}, status=400)

    try:
        appointment = Appointment.objects.get(appointment_id=appointment_id)
    except Appointment.DoesNotExist:
        return Response({"error": "Appointment not found"}, status=404)

    try:
        hospital = Hospital.objects.get(hospital_id=hospital_id)
    except Hospital.DoesNotExist:
        return Response({"error": "Hospital not found"}, status=404)

    #  assign hospital if not already
    appointment.hospital = hospital

    #  update status2
    appointment.status2 = "hospital_approved"
    appointment.save()

    return Response({"message": "Hospital approved successfully"})