from django.contrib import admin
from .models import Movie, Language, Genre, Show, Screen, Seat

admin.site.register(Movie)
admin.site.register(Language)
admin.site.register(Genre)
admin.site.register(Show)
admin.site.register(Screen)
admin.site.register(Seat)
