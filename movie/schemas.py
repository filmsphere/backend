from ninja import Schema
from datetime import datetime
from typing import List

# MODEL SCHEMA ---------------------------------

class GenreSchema(Schema):
    id: int
    name: str

class LanguageSchema(Schema):
    id: int
    name: str

class MovieSchema(Schema):
    imdb_id: str
    title: str
    description: str
    duration: int
    poster: str
    backdrop: str
    release_datetime: str
    imdb_page: str
    genre: List[GenreSchema]
    language: LanguageSchema

class ScreenSchema(Schema):
    number: int
    layout: dict

class SeatSchema(Schema):
    uuid: str
    id: str
    row: str
    col: int
    state: str
    type: str

class ShowSchema(Schema):
    id: int
    date_time: datetime
    movie: MovieSchema
    screen: ScreenSchema
    base_price: float

class ShowListSchema(Schema):
    id: int
    date_time: datetime
    movie: MovieSchema
    base_price: float

# ----------------------------------------------

class ShowSchemaOut(Schema):
    id: int
    date_time: datetime
    base_price: float

class ShowSeatsSchemaOut(Schema):
    success: bool
    message: List[SeatSchema]

class AddShowSchemaIn(Schema):
    imdb_id: str
    screen_number: int
    date_time: datetime
    base_price: int

### RESPONSE SCHEMA ------------------------------

class StringResponsesOut(Schema):
    success: bool
    message: str = "success-msg / error"

class ListMoviesResponseSchemaOut(Schema):
    success: bool
    message: List[MovieSchema]

class ListShowResponseSchemaOut(Schema):
    success: bool
    message: List[ShowSchemaOut]

class MovieResponseSchemaOut(Schema):
    success: bool
    message: MovieSchema

class AddScreenResponseSchemaOut(Schema):
    success: bool
    message: ScreenSchema

class AddShowResponseSchemaOut(Schema):
    success: bool
    message: ShowSchema

