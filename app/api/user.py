from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from app.core.schemas import loginPayload, signupPayload
from app.database import models 
from app.auth.validator import is_valid_email, check_password_strength
from app.auth.security import hash_password, verify_password
from app.database.database import SessionLocal
from sqlalchemy import select 

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

        db.refresh(user)
        user_id = user.id
    finally:
        db.close()

    return {"message": "User created successfully", "user_id": user_id}


@user_router.post("/login")
async def login(payload: loginPayload):

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

        user_id = user.id
    finally:
        db.close()

    return {"message": "Login successful", "user_id": user_id}