from ninja import Schema
from typing import List, Optional
from movie.schemas import *
from core.schemas import UserSchema
from datetime import datetime

class CreateBookingSchemaIn(Schema):
    show_id: str
    seat_uuids: List[str]

class draftBookingSchemaOut(Schema):
    id: str
    show: Optional[ShowListSchema] = None
    created_at: datetime
    seats: List[SeatSchema]
    
class BookingSchemeOut(Schema):
    id: str
    show: Optional[ShowListSchema] = None
    seats: List[SeatSchema]
    total_amount: float

class Booleaan(Schema):
    success: bool
    message: str = "success-msg / ERROR"
class AllUserBookingsSchemaOut(Schema):
    id: str
    movie_title: str
    show_date: datetime
    seats: str
    total_amount: float

class BookingSchema(Schema):
    id: str
    show: ShowListSchema
    seats: List[SeatSchema]
    total_amount: float
    user: UserSchema

class TicketSchema(Schema):
    id: str
    movie_title: str
    show_date: datetime
    seats: str
    total_amount: float

# RESPONSES SCHEMA ----------------------------------

class AllUserBookingsSchemaOutList(Booleaan):
    message: List[AllUserBookingsSchemaOut]

class UserBookingsSchemaOut(Booleaan):
    message: List[BookingSchemeOut]

class UserDraftBookingSchemaOut(Booleaan):
    message: List[draftBookingSchemaOut] = []

class CreateBookingSchemaOut(Booleaan):
    message: draftBookingSchemaOut

class ConfirmBookingSchemaOut(Booleaan):
    message: BookingSchemeOut

class ListBookingsSchemaOut(Booleaan):
    message: List[BookingSchema]

class TicketsSchemaOut(Booleaan):
    message: TicketSchema

# ----------------------------------

class GetAllSchemaOut(Schema):
    movies: List[MovieSchema]
    shows: List[ShowSchema]
    screens: List[ScreenSchema]
    bookings: List[BookingSchema]

class GetAllResponseSchemaOut(Schema):
    success: bool
    message: GetAllSchemaOut
