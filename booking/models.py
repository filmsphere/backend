from django.db import models
from movie.models import Show, Seat
from core.models import User
import string
import secrets

def generate_booking_id(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

class Booking(models.Model):
    id = models.CharField(max_length=16, primary_key=True, unique=True, editable=False, default=generate_booking_id)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seats = models.ManyToManyField(Seat)
    total_amount = models.FloatField()

    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.show.movie.title}"

class draftBooking(models.Model):
    id = models.CharField(max_length=16, primary_key=True, unique=True, editable=False, default=generate_booking_id)
    created_at = models.DateTimeField(auto_now_add=True)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seats = models.ManyToManyField(Seat)

    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.show.movie.title}"

class allUserBookings(models.Model):
    id = models.CharField(max_length=16, primary_key=True, unique=True, editable=False)
    movie_title = models.CharField(max_length=100)
    show_date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seats = models.CharField(max_length=100)
    total_amount = models.FloatField()

    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.movie_title}"