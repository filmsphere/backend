import pyotp
from django.core.mail import send_mail
from dotenv import load_dotenv
import os

load_dotenv()

def generate_otp_secret():
    return pyotp.random_base32()

def generate_otp(secret):
    totp = pyotp.TOTP(secret, interval=300)
    return totp.now()

def send_otp(email, otp, ip_address):
    subject = '🔑 OTP Verification for FilmSphere'
    
    html_message = f"""
    <div style="max-width: 500px; margin: auto; font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
        <div style="text-align: center;">
            <h2 style="color: #333;">🎬 FilmSphere OTP Verification</h2>
        </div>
        <div style="background: white; padding: 20px; border-radius: 8px;">
            <p style="font-size: 16px; color: #555;">Hello,</p>
            <p style="font-size: 16px; color: #555;">Thank you for using <strong>FilmSphere</strong>. Your OTP code is:</p>
            <p style="font-size: 24px; font-weight: bold; color: #e74c3c; text-align: center; padding: 10px; background: #f2f2f2; border-radius: 8px;">{otp}</p>
            <p style="font-size: 14px; color: #888;">IP Address: <strong>{ip_address}</strong></p>
            <p style="font-size: 14px; color: #888;">If you did not request this OTP, please ignore this email.</p>
        </div>
        <div style="text-align: center; margin-top: 20px; font-size: 14px; color: #777;">
            <p>Best regards,</p>
            <p><strong>The FilmSphere Team</strong></p>
        </div>
    </div>
    """
    
    send_mail(
        subject, 
        '',
        os.getenv('EMAIL_HOST_USER'), 
        [email], 
        html_message=html_message
    )
