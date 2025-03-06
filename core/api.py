import pyotp
from . import schemas
from .models import User
from .utils import generate_otp_secret, generate_otp, send_otp
from ninja import NinjaAPI
from ninja.security import django_auth
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login, logout
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.http import JsonResponse
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
import logging
core_logger = logging.getLogger('core')

api = NinjaAPI(csrf=True, urls_namespace='core', 
               throttle= [
                     AnonRateThrottle('5/s'),
                     AuthRateThrottle('10/s')
               ]
)

@api.exception_handler(Ratelimited)
def rate_limit_exception_handler(request, exception):
    return api.create_response(
        request,
        {"success": False, "message": "Too many requests."},
        status=429
    )


# EXAMPLE API
@api.get("/add", auth=django_auth)
@ratelimit(key='user', rate='10/m', method='GET', block=True)
@ratelimit(key='user', rate='50/h', method='GET', block=True)
def add(request, a: int, b: int):
    return {"success": True, "message": a + b}

# TO FETCH USER DETAILS (LOGIN REQUIRED)
@api.get("/user", auth=django_auth, response=schemas.UserDetailSchemaOut)
@ratelimit(key='user', rate='15/m', method='GET', block=True)
@ratelimit(key='user', rate='100/h', method='GET', block=True)
def user(request):
    try:
        is_superuser = request.user.is_superuser
        if is_superuser:
            return {
                "success": True,
                "username": request.user.username,
                "fullname": request.user.fullname,
                "email": request.user.email,
                "balance": request.user.balance,
                "is_superuser": True
            }
        else:
            return {
                "success": True,
                "username": request.user.username,
                "fullname": request.user.fullname,
                "email": request.user.email,
                "balance": request.user.balance,
                "is_superuser": False
            }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# GET CSRF TOKEN
@api.get("/set-csrf-token", response=schemas.CSRFTokenSchemaOut)
@ratelimit(key='user', rate='5/m', method='GET', block=True)
@ratelimit(key='user', rate='50/h', method='GET', block=True)
def get_csrf_token(request):
    try:
        csrf_token = get_token(request)
        if csrf_token:
            return {"success": True, "message": csrf_token}
        else:
            return JsonResponse({"success": False, "message": "CSRF token not found"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# TO REFILL BALANCE
@api.post("/refill-balance", auth=django_auth)
@ratelimit(key='user', rate='1/10m', method='POST', block=True)
def refill_balance(request):
    try:
        request.user.balance = 1500
        request.user.save()
        return {"success": True, "message": request.user.balance}
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# LOGIN
@api.post("/login", response=schemas.StringResponsesOut)
@ratelimit(key='user', rate='5/m', method='POST', block=True)
@ratelimit(key='user', rate='30/h', method='POST', block=True)
def login_view(request, payload: schemas.SignInSchema):
    core_logger.info(f"User {payload.username} is trying to login")
    try:
        if payload.username == "" and payload.email == "":
            return JsonResponse({"success": False, "message": "Username or email is required"})
        elif payload.password == "":
            return JsonResponse({"success": False, "message": "Password is required"})
        elif payload.username == "" and payload.email != "":
            user = authenticate(request, email=payload.email, password=payload.password)
        else:
            user = authenticate(request, username=payload.username, password=payload.password)

        if user is not None:
            login(request, user)
            return JsonResponse({"success": True, "message": "Logged in successfully"})
        else:
            return JsonResponse({"success": False, "message": "Invalid credentials"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# LOGOUT (LOGIN IS REQUIRED)
@api.post("/logout", auth=django_auth, response=schemas.StringResponsesOut)
@ratelimit(key='user', rate='5/m', method='POST', block=True)
@ratelimit(key='user', rate='30/h', method='POST', block=True)
def logout_view(request):
    try:
        if request.user.is_authenticated:
            logout(request)
            return JsonResponse({"success": True, "message": "Logged out"})
        else:
            return JsonResponse({"success": False, "message": "User is not logged in"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# REQUEST-OTP
@api.post("/request-otp/{email}", response=schemas.StringResponsesOut)
@ratelimit(key='user', rate='1/m', method='POST', block=True)
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def request_otp(request, email):
    core_logger.info(f"User {email} has requested for OTP")
    try: 
        if User.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "message": "Email is already taken"})

        otp_secret = generate_otp_secret()

        # Generate OTP valid for 5 minutes
        otp = generate_otp(otp_secret)

        # Get the IP address from the request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Store the OTP secret in the session
        request.session['otp_secret'] = otp_secret
        request.session['otp_email'] = email

        # Send OTP to the user's email
        send_otp(email, otp, ip_address)
        return JsonResponse({"success": True, "message": "OTP sent successfully"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500) 

# REGISTER
@api.post("/register", response=schemas.StringResponsesOut)
@ratelimit(key='user', rate='5/m', method='POST', block=True)
@ratelimit(key='user', rate='20/h', method='POST', block=True)
def register(request, payload: schemas.RegisterSchemaIn):
    core_logger.info(f"User {payload.username} has requested to register")
    try:
        if User.objects.filter(username=payload.username).exists():
            return JsonResponse({"success": False, "message": "Username is already taken"})
        if User.objects.filter(email=payload.email).exists():
            return JsonResponse({"success": False, "message": "Email is already taken"})

        # Retrieve the OTP secret from the session
        otp_secret = request.session.get('otp_secret')
        otp_email = request.session.get('otp_email')

        if not otp_secret:
            return JsonResponse({"success": False, "message": "OTP secret not found"})

        if otp_email != payload.email:
            return JsonResponse({"success": False, "message": "Email does not match the one used to request the OTP"})

        # Verify the OTP
        totp = pyotp.TOTP(otp_secret, interval=300)
        if totp.verify(payload.otp):
            User.objects.create_user(
                fullname=payload.fullname, 
                username=payload.username, 
                email=payload.email, 
                password=payload.password,
            )
            del request.session['otp_secret']
            del request.session['otp_email']
            return JsonResponse({"success": True, "message": "User registered successfully"})
        else:
            return JsonResponse({"success": False, "message": "Invalid OTP"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# TO CHECK USERNAME AVAILABILITY
@api.get("/check-username/{user_name}", response=schemas.UsernameCheckSchemaOut)
@ratelimit(key='user', rate='30/m', method='GET', block=True)
@ratelimit(key='user', rate='90/h', method='GET', block=True)
def check_username(request, user_name):
    try:
        if User.objects.filter(username=user_name).exists():
            return {"success": False, "message": "taken"}
        return {"success": True, "message": "Username is available"}
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
