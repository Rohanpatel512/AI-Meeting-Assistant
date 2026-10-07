from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Response
from app.core.schemas import loginPayload, signupPayload
from app.database import models 
from app.auth.validator import is_valid_email, check_password_strength
from app.auth.security import hash_password, verify_password, create_access_token, refresh_access_token
from app.database.database import SessionLocal
from sqlalchemy import select 
from app.core.config import JWT_SECRET, JWT_ALGORITHM
from datetime import datetime, timezone, timedelta
import jwt 

user_router = APIRouter(prefix="/user", tags=["Authentication"])

@user_router.post("/signup")
async def signup(payload: signupPayload):

    if not payload.name:
        raise HTTPException(status_code=400, detail="Name is required")

    if not payload.email:
        raise HTTPException(status_code=400, detail="Email is required")

    if not payload.password:
        raise HTTPException(status_code=400, detail="Password is required")

    if not payload.confirm_password:
        raise HTTPException(status_code=400, detail="Confirm password is required")

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Check if email is in proper format and if it already exists in the database
    if not is_valid_email(payload.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    db = SessionLocal()
    try:
        stmt = select(models.User).where(models.User.email == payload.email)
        user_exists = db.execute(stmt).scalars().first()
        if user_exists:
            raise HTTPException(status_code=400, detail="This user already exists")

        # Check if password meets the requirements (length, complexity, etc.)
        if not check_password_strength(payload.password):
            raise HTTPException(status_code=400, detail="Password does not meet the requirements")

        # If all checks pass, create a new user in the database and return a success message 
        user = models.User(name=payload.name, email=payload.email, password=hash_password(payload.password))
        db.add(user)
        db.commit()

        usage = models.Usage(user_id=user.id, total_file_size=0, summary_amount=0)
        db.add(usage)
        db.commit()

        db.refresh(user)
        db.refresh(usage)

    finally:
        db.close()

    return {"message": "User created successfully"}


@user_router.post("/login")
async def login(payload: loginPayload, response: Response):

    # Check if either email or password are empty
    if not payload.email or not payload.password:
        raise HTTPException(status_code=401, detail="Invalid password or email")
        return {"message": "Invalid password or email"}

    
    db = SessionLocal()

    try:
        stmt = select(models.User).where(models.User.email == payload.email)
        user = db.execute(stmt).scalars().first()

        if not user or not verify_password(payload.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid password or user does not exist")
            return {"message": "Invalid password or user does not exist"}

        access_token = create_access_token(user.id)

        response.set_cookie( 
            key="access_token", 
            value=access_token, 
            httponly=True, 
            secure=False, # Set to false on local development, change to true in production 
            samesite="lax", 
            max_age=3600, 
            path="/" 
        )

       
    finally:
        db.close()


    return {"message": "Login successful"}



@user_router.post("/refresh")
async def refresh(request: Request, response: Response):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    exp_time = payload.get("exp")
    current_time = int(datetime.now(timezone.utc).timestamp())

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if not exp_time:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if int(exp_time) <= current_time:
        new_access_token = create_access_token(int(user_id))
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=3600,
            path="/"
        )
        return {"message": "token refreshed"}

    return {"message": "token is still valid"}
