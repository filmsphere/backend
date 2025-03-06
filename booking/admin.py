from django.contrib import admin
from .models import Booking, draftBooking, allUserBookings

admin.site.register(Booking)
admin.site.register(draftBooking)
admin.site.register(allUserBookings)