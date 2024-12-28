from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.db import IntegrityError
from django.http import JsonResponse
from .models import LoginForm ,Home ,StudentID
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
import logging
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.decorators import  throttle_classes


@csrf_exempt
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def loginUser(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

        name = data.get('name')
        email = data.get('email')
        password = data.get('user_password')
        confirm_password = data.get('confirm_password')

        if not all([name, email, password, confirm_password]):
            return JsonResponse({"error": "All fields are required."}, status=400)

        if password != confirm_password:
            return JsonResponse({"error": "Passwords do not match."}, status=400)

        user, created = LoginForm.objects.get_or_create(email=email)
        if not created:
            return JsonResponse({"error": "User with this email already exists."}, status=400)

        user.name = name
        user.user_password = password
        user.confirm_password = confirm_password
        user.save()

        django_user = User.objects.filter(email=email).first() 
        if django_user:
            auth_login(request, django_user)
        else:
            django_user = User.objects.create_user(username=email, email=email, password=password)
            django_user.save()
            auth_login(request, django_user)

        user.generate_otp()

        return JsonResponse({"message": "User created and logged in successfully. OTP sent to email."}, status=200)

    return JsonResponse({"error": "Invalid request method."}, status=405)


logger = logging.getLogger(__name__)
@csrf_exempt
def verify_otp(request, email):
    if request.method == 'POST':
        try:

            data = json.loads(request.body)
            user_otp = data.get('user_otp')
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

        if not user_otp:
            logger.error("OTP not provided in the request.")
            return JsonResponse({"error": "OTP is required."}, status=400)

        logger.debug(f"User OTP received: {user_otp}")
        
        user = get_object_or_404(LoginForm, email=email)

        logger.debug(f"Generated OTP: {user.generated_otp}")
        
        if user.generated_otp == str(user_otp):
            if user.otp_expiry and timezone.now() <= user.otp_expiry:
                user.user_otp = user_otp  
                user.save()
                return JsonResponse({"message": "OTP verified successfully."}, status=200)
            else:
                logger.debug("OTP expired.")
                return JsonResponse({"error": "OTP has expired."}, status=400)
        else:
            logger.debug("OTP does not match.")
            return JsonResponse({"error": "Invalid OTP."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
def getInformation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

        # Access the password from the JSON payload
        password = data.get('user_password')

        # Check if password is provided and is not empty
        if not password:
            return JsonResponse({"error": "Password is required."}, status=400)

        # Continue with the rest of the logic
        college_name = data.get('college_name')
        course = data.get('course')
        year = data.get('year')
        CGPA = data.get('CGPA')
        student_choice = data.get('student_choice')
        cgpa_percentage = data.get('cgpa_percentage')
        cgpa_number = data.get('cgpa_number')
        email = data.get('email')  # Add email to identify the student

        if not email:
            return JsonResponse({"error": "Email is required to identify the student."}, status=400)

        if CGPA == 'percentage' and not cgpa_percentage:
            return JsonResponse({"error": "CGPA percentage is required when CGPA type is 'percentage'."}, status=400)
        elif CGPA == 'cgpa' and not cgpa_number:
            return JsonResponse({"error": "CGPA number is required when CGPA type is 'cgpa'."}, status=400)

        try:
            # Find or create the LoginForm instance for the existing student
            login_form_instance = LoginForm.objects.filter(email=email).first()

            if login_form_instance:
                # If the LoginForm exists, update its password
                login_form_instance.user_password = password
                login_form_instance.save()
            else:
                # If the LoginForm does not exist, create a new one
                login_form_instance = LoginForm.objects.create(email=email, user_password=password)

            # Now update or create the Home instance for the student
            home_instance, created = Home.objects.update_or_create(
                student_name=login_form_instance,  # Associate with LoginForm
                defaults={
                    'college_name': college_name,
                    'course': course,
                    'year': year,
                    'CGPA': CGPA,
                    'student_choice': student_choice,
                    'cgpa_percentage': cgpa_percentage if CGPA == 'percentage' else None,
                    'cgpa_number': cgpa_number if CGPA == 'cgpa' else None,
                }
            )

            # If Home instance is new, save it
            if created:
                home_instance.save()

            # Now create or update the StudentID instance with the correct LoginForm instance
            student_id_instance, created = StudentID.objects.update_or_create(
                student=login_form_instance, 
                defaults={'password': password}
            )

            return JsonResponse({
                "message": "Details saved or updated successfully!",
                "student_id": student_id_instance.unique_id  
            }, status=201)

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except IntegrityError as e:
            return JsonResponse({"error": f"Integrity Error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@csrf_exempt
def signInUser(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            unique_id = data.get('unique_id') 
            password = data.get('password')

            if not unique_id or not password:
                return JsonResponse({"error": "Unique ID and password are required."}, status=400)

            try:
                student_id_instance = StudentID.objects.get(unique_id=unique_id) 
                if student_id_instance.password == password:  
                    return JsonResponse({"message": "Sign in successful!"}, status=200)
                else:
                    return JsonResponse({"error": "Invalid password."}, status=401)
            except StudentID.DoesNotExist:
                return JsonResponse({"error": "Unique ID does not exist."}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

