from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from dotenv import load_dotenv
import os
import qrcode
from io import BytesIO
from email.mime.image import MIMEImage

load_dotenv()

def send_tickets(username, email, booking_id, movie_title, movie_language, start_time, total_price, seat_ids):
    subject = '🎬 Filmsphere Movie Tickets'
    seats = ', '.join(seat_ids)
    date = start_time.strftime('%d-%m-%Y')
    start_time = start_time.strftime('%I:%M %p')

    qr = qrcode.make(f"https://www.filmsphere.me/tickets/{booking_id}")
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    text_content = f"Hello {username},\nYour ticket link: https://www.filmsphere.com/tickets/{booking_id}\nEnjoy the movie!"
    html_content = f"""
    <div style="max-width: 500px; margin: auto; font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
        <div style="text-align: center;">
            <h2 style="color: #333;">🎬 Filmsphere Movie Tickets</h2>
        </div>
        <div style="background: white; padding: 20px; border-radius: 8px;">
            <p style="font-size: 16px; color: #555;">Hello {username},</p>
            <p style="font-size: 16px; color: #555;">Thank you for using <strong>FilmSphere</strong>. Here is your ticket link:</p>
            <p style="font-size: 24px; font-weight: bold; color: #e74c3c; text-align: center; padding: 10px; background: #f2f2f2; border-radius: 8px;">
                <a href="https://www.filmsphere.me/tickets/{booking_id}">www.filmsphere.me/ticket/{booking_id}</a>
            </p>
            <p style="font-size: 16px; color: #555;">Show the QR code below at the Movie Theatre:</p>
            <div style="text-align: center;">
                <img src="cid:qr_code" alt="QR Code" style="width: 200px; height: 200px; border: 2px solid #ddd; padding: 5px; border-radius: 8px;">
            </div>
            <p style="font-size: 16px; color: #555;">Your booking details:</p>
            <p style="font-size: 16px; color: #555;"><strong>Movie:</strong> {movie_title} [{movie_language}]</p>
            <p style="font-size: 16px; color: #555;"><strong>Date:</strong> {date}</p>
            <p style="font-size: 16px; color: #555;"><strong>Time:</strong> {start_time}</p>
            <p style="font-size: 16px; color: #555;"><strong>Seats:</strong> {seats}</p>
            <p style="font-size: 16px; color: #555;"><strong>Total price:</strong> {total_price} Coins</p>
            
            <p style="font-size: 16px; color: #555;">Enjoy the movie!</p>
        </div>
        <div style="text-align: center; margin-top: 20px; font-size: 14px; color: #777;">
            <p>Best regards,</p>
            <p><strong>The FilmSphere Team</strong></p>
        </div>
    </div>
    """

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        os.getenv('EMAIL_HOST_USER'),
        [email]
    )
    msg.attach_alternative(html_content, "text/html")

    mime_image = MIMEImage(buffer.getvalue(), _subtype="png")
    mime_image.add_header('Content-ID', '<qr_code>')
    mime_image.add_header('Content-Disposition', 'inline', filename="qr_code.png")
    msg.attach(mime_image)

    msg.send()
