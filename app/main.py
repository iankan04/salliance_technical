from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.auth import router as auth_router, user_store
from app.scrape import scrape_linkedin_profile
from app.models import UserProfile

app = FastAPI()

# Mount the auth router
app.include_router(auth_router, prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/linkedin")

@app.get("/")
async def root():
    return { "message": "Welcome to your server. Go to /auth/linkedin to start authentication" }