import os
from ninja import NinjaAPI
from ninja.security import django_auth, django_auth_superuser
from django_ratelimit.decorators import ratelimit
from . import schemas, utils
from .models import *
from django_ratelimit.exceptions import Ratelimited
from movie.models import Movie, Show, Screen, Seat
from movie import schemas as movieSchema
from datetime import datetime, timezone, timedelta
from django.http import JsonResponse, response
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
import logging
booking_logger = logging.getLogger('booking')

api = NinjaAPI(csrf=True, urls_namespace='booking',
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

@api.get("/add", auth=django_auth)
@ratelimit(key='user', rate='5/m', method='GET', block=True)
@ratelimit(key='user', rate='100/h', method='GET', block=True)
def add(request, a: int, b: int):
    return {"result": a + b}

@api.get("/get-user-bookings", auth=django_auth, response=schemas.AllUserBookingsSchemaOutList)
@ratelimit(key='user', rate='10/m', method='GET', block=True)
@ratelimit(key='user', rate='100/h', method='GET', block=True)
def get_user_bookings(request):
    try:
        allbookings = allUserBookings.objects.filter(user=request.user)
        allbookings = allbookings[::-1]
        return {
            "success": True,
            "message": [schemas.AllUserBookingsSchemaOut.from_orm(booking) for booking in allbookings],
        }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.get("/get-user-draft-bookings", auth=django_auth, response=schemas.UserDraftBookingSchemaOut)
@ratelimit(key='user', rate='15/m', method='GET', block=True)
@ratelimit(key='user', rate='150/h', method='GET', block=True)
def get_user_draft_bookings(request):
    try:
        draft_bookings = draftBooking.objects.filter(user=request.user)
        return {
            "success": True,
            "message": [schemas.draftBookingSchemaOut.from_orm(booking) for booking in draft_bookings]
        }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.post("/create-booking", auth=django_auth, response=schemas.CreateBookingSchemaOut)
@ratelimit(key='user', rate='5/m', method='POST', block=True)
@ratelimit(key='user', rate='30/h', method='POST', block=True)
def create_booking(request, payload: schemas.CreateBookingSchemaIn):
    booking_logger.info(f"User {request.user.username} has created a draft booking")
    try:
        user = request.user
        show = Show.objects.get(id=payload.show_id)
        seats = Seat.objects.filter(uuid__in=payload.seat_uuids)
        if not show or not seats:
            return JsonResponse({
                "success": False,
                "message": "Couldn't find show or seats."
            })
        for seat in seats:
            if seat.state != 'available':
                return JsonResponse({
                        "success": False,
                        "message": "Seat not available"
                })

        if draftBooking.objects.filter(user=user).exists():
            return JsonResponse({
                    "success": False,
                    "message": "You already have a Pending Booking"
            })
        else:
            draft_booking = draftBooking.objects.create(show=show, user=user)
            draft_booking.seats.set(seats)

        for seat in seats:
            seat.state = 'locked'
            seat.locked_at = datetime.now(timezone.utc)
            seat.save()

        return {
            "success": True,
            "message": schemas.draftBookingSchemaOut.from_orm(draft_booking)
        }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.post("/confirm-booking/{draft_show_id}", auth=django_auth, response=schemas.ConfirmBookingSchemaOut)
@ratelimit(key='user', rate='4/m', method='POST', block=True)
@ratelimit(key='user', rate='30/h', method='POST', block=True)
def confirm_booking(request, draft_show_id: str):
    booking_logger.info(f"User {request.user.username} has confirmed a booking")
    try:
        draft_booking = draftBooking.objects.get(id=draft_show_id)
        if not draft_booking:
            return JsonResponse({
                "success": False,
                "message": "Pending Booking doesn't exists"
            })
        elif not draftBooking.objects.filter(user=request.user).exists():
            return JsonResponse({
                    "success": False,
                    "message": "Create a booking before confirm"
            })
        elif request.user != draft_booking.user:
            return JsonResponse({
                "success": False,
                "message": "This Pending Booking doesn't belongs to you"
            })

        show = draft_booking.show
        if not show:
            return JsonResponse({
                "success": False,
                "message": "Show doesn't exists"
            })
        seats = draft_booking.seats.all()

        total_price = 0
        for seat in seats:
            total_price += seat.price

        total_price *= show.base_price

        if request.user.balance < total_price:
            return {
                    "success": False,
                    "message": "Insufficient Balance"
            }

        draft_booking = draftBooking.objects.get(user=request.user)
        draft_booking.delete()

        request.user.balance -= total_price
        request.user.save()

        booking = Booking.objects.create(show=show, user=request.user, total_amount=total_price)
        booking.seats.set(seats)
        booking.save()

        seats_str = ""

        for seat in seats:
            seat.state = 'booked'
            seat.locked_at = None
            seat.save()
            seats_str += seat.id + " "

        new_booking = allUserBookings.objects.create(id=booking.id, movie_title=show.movie.title, show_date=show.date_time, user=request.user, total_amount=total_price, seats=seats_str)

        return {"success": True, "message": schemas.BookingSchemeOut.from_orm(booking)}
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.get("/delete-draft-booking/{booking_id}", auth=django_auth, response=schemas.Booleaan)
@ratelimit(key='user', rate='5/m', method='GET', block=True)
@ratelimit(key='user', rate='100/h', method='GET', block=True)
def delete_draft_booking(request, booking_id: str):
    try:
        draft_booking = draftBooking.objects.get(id=booking_id)
        if draft_booking:
            if draft_booking.user != request.user:
                return JsonResponse({
                        "success": False,
                        "message": "Unauthorized"
                })
            seats = draft_booking.seats.all()
            for seat in seats:
                seat.state = 'available'
                seat.locked_at = None
                seat.save()
            draft_booking.delete()
            return {
                    "success": True,
                    "message": "Successfully Deleted"
            }
        else:
            return JsonResponse({
                    "success": False,
                    "message": "Pending Booking does not exists"
            })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.post("/cancel-booking/{booking_id}", auth=django_auth, response=schemas.Booleaan)
@ratelimit(key='user', rate='5/m', method='POST', block=True)
@ratelimit(key='user', rate='80/h', method='POST', block=True)
def cancel_booking(request, booking_id: str):
    booking_logger.info(f"User {request.user.username} has requested to cancel booking")
    try:
        booking = Booking.objects.get(id=booking_id)
        if booking.user != request.user:
            return JsonResponse({
                    "success": False,
                    "message": "Unauthorized"
            })
        if booking.show.date_time < datetime.now(timezone.utc) + timedelta(minutes=20):
            return JsonResponse({
                    "success": False,
                    "message": "Too late to cancel"
            })
        seats = booking.seats.all()
        total_price = booking.total_amount
        for seat in seats:
            seat.state = 'available'
            seat.locked_at = None
            seat.save()
        booking.delete()

        newbooking = allUserBookings.objects.get(id=booking_id)
        newbooking.delete()

        refund_amount = total_price * 0.8
        request.user.balance += refund_amount
        request.user.save()
        return {"success": True, "message": f"Refund: {refund_amount}"}
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.get("/send-tickets/{booking_id}", auth=django_auth, response=schemas.Booleaan)
@ratelimit(key='user', rate='2/m', method='GET', block=True)
@ratelimit(key='user', rate='4/5m', method='GET', block=True)
@ratelimit(key='user', rate='10/h', method='GET', block=True)
def send_email(request, booking_id: str):
    booking_logger.info(f"User {request.user.username} has requested to send tickets")
    try:
        booking = Booking.objects.get(id=booking_id)
        seat_ids = []
        for seat in booking.seats.all():
            seat_ids.append(seat.id)
        utils.send_tickets(booking.user.username, booking.user.email, booking.id, booking.show.movie.title, booking.show.movie.language, booking.show.date_time, booking.total_amount, seat_ids)
        return {"success": True, "message": "Email sent."}
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.get("/get-booking-details/{booking_id}", response=schemas.TicketsSchemaOut)
@ratelimit(key='user', rate='10/m', method='GET', block=True)
@ratelimit(key='user', rate='150/h', method='GET', block=True)
def get_booking_details(request, booking_id: str):
    try:
        booking = allUserBookings.objects.get(id=booking_id)
        if booking:
            return {"success": True, "message": schemas.TicketSchema.from_orm(booking)}
        else:
            return JsonResponse({
                    "success": False,
                    "message": "Booking does not exists"
            })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.get("/list-bookings/{show_id}", auth=django_auth_superuser, response=schemas.ListBookingsSchemaOut)
@ratelimit(key='user', rate='10/m', method='DELETE', block=True)
@ratelimit(key='user', rate='100/h', method='DELETE', block=True)
def list_bookings(request, show_id: int):
    try:
        bookings = Booking.objects.filter(show__id=show_id)
        return {
            "success": True,
            "message": [schemas.BookingSchema.from_orm(booking) for booking in bookings]
        }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.get("/delete-booking/{booking_id}", auth=django_auth_superuser, response=schemas.Booleaan)
@ratelimit(key='user', rate='10/m', method='DELETE', block=True)
@ratelimit(key='user', rate='100/h', method='DELETE', block=True)
def delete_booking(request, booking_id: str):
    try:
        booking = Booking.objects.get(id=booking_id)
        seats = booking.seats.all()
        for seat in seats:
            seat.state = 'available'
            seat.locked_at = None
            seat.save()
        booking.delete()

        newbooking = allUserBookings.objects.get(id=booking_id)
        newbooking.delete()
        return {
            "success": True,
            "message": "Booking deleted successfully"
        }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@api.get("/getall", auth=django_auth_superuser, response=schemas.GetAllResponseSchemaOut)
@ratelimit(key='user', rate='20/m', method='GET', block=True)
@ratelimit(key='user', rate='150/h', method='GET', block=True)
def getall(request):
    try:
        movies = Movie.objects.all()
        screens = Screen.objects.all()
        shows = Show.objects.all()
        bookings = Booking.objects.all()
        return {
            "success": True,
            "message": {
            "movies": [movieSchema.MovieSchema.from_orm(movie) for movie in movies],
            "shows": [movieSchema.ShowSchema.from_orm(show) for show in shows],
            "screens": [movieSchema.ScreenSchema.from_orm(screen) for screen in screens],
            "bookings": [schemas.BookingSchema.from_orm(booking) for booking in bookings]
            }
        }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
