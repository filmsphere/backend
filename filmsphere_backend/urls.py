from django.contrib import admin
from django.urls import path
from core.api import api as core_api
from movie.api import api as movie_api
from booking.api import api as booking_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", core_api.urls),
    path("movie/", movie_api.urls),
    path("booking/", booking_api.urls),
]