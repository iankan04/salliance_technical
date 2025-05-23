from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.auth import router as auth_router
from app.scrape import scrape_linkedin_profile
from app.models import UserProfile

app = FastAPI()
app.include_router(auth_router, prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/linkedin")

@app.get("/user")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if "current_user" not in user_store:
        raise HTTPException(status_code=404, detail="User not found")
    return user_store["current_user"]

@app.get("/skills")
async def get_skills(linkedin_url: str, token: str = Depends(oauth2_scheme)):
    try:
        skills = scrape_linkedin_profile(linkedin_url)
        return {"skills": skills}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))