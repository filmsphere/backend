from django.utils.translation.trans_real import reset_cache
from ninja import NinjaAPI
from ninja.security import django_auth, django_auth_superuser
from . import schemas
from .models import Movie, Language, Genre, Show, Screen, Seat
from booking.models import Booking, draftBooking
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from datetime import datetime, timedelta
from django.utils.timezone import timezone
from django.http import JsonResponse
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
import os
import logging
movie_logger = logging.getLogger('movie')

api = NinjaAPI(csrf=True, urls_namespace='movie',
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
def add(request, a: int, b: int):
    return {"result": a + b}

@api.get("/list-movies", auth=django_auth, response=schemas.ListMoviesResponseSchemaOut)
@ratelimit(key='user', rate='20/m', method='GET', block=True)
@ratelimit(key='user', rate='100/h', method='GET', block=True)
def list_movies(request):
    try:
        movies = Movie.objects.all()
        return {"success": True, "message": [schemas.MovieSchema.from_orm(movie) for movie in movies]}
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.get("/get-movie-shows/{imdb_id}", auth=django_auth, response=schemas.ListShowResponseSchemaOut)
@ratelimit(key='user', rate='20/m', method='GET', block=True)
@ratelimit(key='user', rate='150/h', method='GET', block=True)
def get_movie_shows(request, imdb_id: str):
    try:
        movie = Movie.objects.get(imdb_id=imdb_id)
        shows = Show.objects.filter(movie=movie)
        return {
            "success": True,
            "message": [schemas.ShowSchema.from_orm(show) for show in shows]
        }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.get("/get-show-seats/{show_id}", auth=django_auth, response=schemas.ShowSeatsSchemaOut)
@ratelimit(key='user', rate='20/m', method='GET', block=True)
@ratelimit(key='user', rate='100/h', method='GET', block=True)
def get_show_seats(request, show_id: int):
    try:
        show = Show.objects.get(id=show_id)
        seats = Seat.objects.filter(show=show)

        return {
            "success": True,
            "message": [schemas.SeatSchema.from_orm(seat) for seat in seats]
        }
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

############################################################################

# ADMIN ACTIONS

# DEPRECATED
# @api.get("/get-imdb-movie-details", auth=django_auth_superuser)
# @ratelimit(key='user', rate='20/m', method='GET', block=True)
# @ratelimit(key='user', rate='100/h', method='GET', block=True)
# async def get_movie_details(request, imdb_id: str):
#     movie = await get_movie(imdb_id)
#     return {"movie": movie}


@api.post("/add-movie", auth=django_auth_superuser, response=schemas.MovieResponseSchemaOut)
@ratelimit(key='user', rate='10/m', method='POST', block=True)
@ratelimit(key='user', rate='100/h', method='POST', block=True)
def create_movie(request, payload: schemas.MovieSchema):
    movie_logger.info(f"Adding Movie: {payload.title}")
    try:
        if Movie.objects.filter(title=payload.title).exists() or Movie.objects.filter(imdb_id=payload.imdb_id).exists():
            return JsonResponse({"success": False, "message": "Movie already exists."})

        if not Language.objects.filter(name=payload.language.name).exists():
            language = Language.objects.create(name=payload.language.name)
        else:
            language = Language.objects.get(name=payload.language.name)

        genre_ids = []
        for genre in payload.genre:
            if not Genre.objects.filter(name=genre.name).exists():
                genre_obj = Genre.objects.create(name=genre.name)
            else:
                genre_obj = Genre.objects.get(name=genre.name)
            genre_ids.append(genre_obj.id)

        movie = Movie.objects.create(
            imdb_id=payload.imdb_id,
            title=payload.title,
            description=payload.description,
            duration=payload.duration,
            poster=payload.poster,
            backdrop=payload.backdrop,
            release_datetime=payload.release_datetime,
            imdb_page=payload.imdb_page,
            language=language
        )
        movie.genre.set(genre_ids)
        if Movie.objects.filter(imdb_id=movie.imdb_id).exists():
            return {"success": True, "message": schemas.MovieSchema.from_orm(movie)}
        else:
            return JsonResponse({"success": False, "message": "Error in Adding a new Movie"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.delete("/delete-movie/{imdb_id}", auth=django_auth_superuser, response=schemas.StringResponsesOut)
@ratelimit(key='user', rate='10/m', method='DELETE', block=True)
@ratelimit(key='user', rate='50/h', method='DELETE', block=True)
def delete_movie(request, imdb_id: str):
    try:
        movie = Movie.objects.filter(imdb_id=imdb_id)
        if movie.exists():
            movie.delete()
            return {"success": True, "message": "Movie deleted successfully."}
        else:
            return JsonResponse({"success": False, "message": "Movie not found."})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.post("/add-screen", auth=django_auth_superuser, response=schemas.AddScreenResponseSchemaOut)
@ratelimit(key='user', rate='50/m', method='POST', block=True)
@ratelimit(key='user', rate='100/h', method='POST', block=True)
def add_screen(request, payload: schemas.ScreenSchema):
    movie_logger.info(f"Adding Screen: {payload.number}")
    try:
        if Screen.objects.filter(number=payload.number).exists():
            return {"success": False, "message": f"Screen {payload.number} already exists."}
        else:
            screen = Screen.objects.create(
                number=payload.number,
                layout=payload.layout
            )
            return {"success": True, "message": schemas.ScreenSchema.from_orm(screen)}
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.delete("/delete-screen/{number}", auth=django_auth_superuser, response=schemas.StringResponsesOut)
@ratelimit(key='user', rate='10/m', method='DELETE', block=True)
@ratelimit(key='user', rate='50/h', method='DELETE', block=True)
def delete_screen(request, number: int):
    try:
        screen = Screen.objects.filter(number=number)
        if screen.exists():
            screen.delete()
            return {"success": True, "message": "Screen deleted successfully."}
        else:
            return JsonResponse({"success": False, "message": "Screen not found."})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.post("/add-show", auth=django_auth_superuser, response=schemas.AddShowResponseSchemaOut)
@ratelimit(key='user', rate='50/m', method='POST', block=True)
@ratelimit(key='user', rate='100/h', method='POST', block=True)
def add_show(request, payload: schemas.AddShowSchemaIn):
    movie_logger.info(f"Adding Show for: {payload.imdb_id}")
    try:
        if not all([payload.imdb_id, payload.screen_number, payload.date_time, payload.base_price]):
            return JsonResponse({"success": False, "message": "All fields are required."})
        movie = Movie.objects.get(imdb_id=payload.imdb_id)
        if not movie:
            return JsonResponse({"success": False, "message": "Movie does not exists."})
        screen = Screen.objects.get(number=payload.screen_number)
        if not screen:
            return JsonResponse({"success": False, "message": "Screen does not exists."})

        if payload.date_time < datetime.now(timezone.utc):
            return {"success": False, "message": "Show time is in past."}

        overlapping_shows = Show.objects.filter(
            screen__number=payload.screen_number,
            date_time__range=(payload.date_time - timedelta(minutes=180), payload.date_time + timedelta(minutes=180))
        )
        if overlapping_shows.exists():
            return JsonResponse({"success": False, "message": "This show overlaps with another show."})

        show = Show.objects.create(
            date_time=payload.date_time,
            movie=movie,
            screen=screen,
            base_price=payload.base_price
        )
        for row in screen.layout['rows']:
            for seat in row['seats']:
                Seat.objects.create(
                    id = seat['id'],
                    type = seat['type'],
                    row = seat['id'][0],
                    col = int(seat['id'][1:]),
                    show = show,
                    state = 'booked' if seat['type'] == 'disabled' else 'available',
                    price = 1 if seat['type'] == 'standard' else 1.5 if seat['type'] == 'premium' else 2 if seat['type'] == 'vip' else 0
        )
        if Show.objects.get(id=show.id):
            return {"success": True, "message": schemas.ShowSchema.from_orm(show)}
        else:
            return JsonResponse({"success": False, "message": "Adding Show failed."})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api.delete("/delete-show/{show_id}", auth=django_auth_superuser, response=schemas.StringResponsesOut)
@ratelimit(key='user', rate='50/m', method='DELETE', block=True)
@ratelimit(key='user', rate='100/h', method='DELETE', block=True)
def delete_show(request, show_id: int):
    try:
        show = Show.objects.get(id=show_id)
        if show:
            show.delete()
            return {"success": True, "message": "Show deleted successfully."}
        else:
            return JsonResponse({"success": False, "message": "Show not found."})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
