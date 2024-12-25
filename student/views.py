from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.http import JsonResponse
from .models import LoginForm ,Home
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
        college_name = request.POST.get('college_name')
        course = request.POST.get('course')
        year = request.POST.get('year')
        CGPA = request.POST.get('CGPA')
        student_choice = request.POST.get('student_choice')
        cgpa_percentage = request.POST.get('cgpa_percentage')
        cgpa_number = request.POST.get('cgpa_number')

        # Validate that either cgpa_percentage or cgpa_number is provided based on CGPA type
        if CGPA == 'percentage' and not cgpa_percentage:
            return JsonResponse({"error": "CGPA percentage is required when CGPA type is 'percentage'."}, status=400)
        elif CGPA == 'cgpa' and not cgpa_number:
            return JsonResponse({"error": "CGPA number is required when CGPA type is 'cgpa'."}, status=400)

        # Create the Home object
        try:
            home_instance = Home(
                college_name=college_name,
                course=course,
                year=year,
                CGPA=CGPA,
                student_choice=student_choice,
                cgpa_percentage=cgpa_percentage if CGPA == 'percentage' else None,
                cgpa_number=cgpa_number if CGPA == 'cgpa' else None,
            )
            home_instance.save()
            return JsonResponse({"message": "Home details saved successfully!"}, status=201)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)
