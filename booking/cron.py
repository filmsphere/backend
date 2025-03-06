from .models import Show, draftBooking
from datetime import datetime, timedelta

def cron_delete_show():
    shows = Show.objects.filter(date_time__lt=datetime.now())
    if shows.exists():
        for show in shows:
            show.delete()

def cron_delete_draft_booking():
    draft_bookings = draftBooking.objects.filter(created_at__lt=datetime.now() - timedelta(minutes=5))
    for draft_booking in draft_bookings:
        for seat in draft_booking.seats.all():
            seat.state = 'available'
            seat.save()

    for draft_booking in draft_bookings:
        draft_booking.delete()