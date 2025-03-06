from ninja import Schema
from .models import User

class SignInSchema(Schema):
    username: str = ""
    email: str = ""
    password: str

class RegisterSchemaIn(Schema):
    fullname: str
    username: str
    email: str
    password: str
    otp: str

class UserDetailSchemaOut(Schema):
    success: bool
    username: str
    fullname: str
    email: str
    balance: int = 1500
    is_superuser: bool

class StringResponsesOut(Schema):
    success: bool
    message: str = "Success-msg / ERROR"

class CSRFTokenSchemaOut(StringResponsesOut):
    message: str = "CSRF-TOKEN / ERROR"

class UsernameCheckSchemaOut(StringResponsesOut):
    message: str = " 'taken' / ERROR"

class UserSchema(Schema):
    username: str
    fullname: str
    email: str
    balance: int
