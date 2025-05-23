from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import requests
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# In-memory storage (replace with database in production)
user_store = {}
token_store = {}

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/auth/linkedin/callback"

@router.get("/auth/linkedin")
async def login_linkedin():
    # Step 1: Redirect user to LinkedIn for authorization
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&client_id={LINKEDIN_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&state=random_state&"
        f"scope=r_liteprofile%20r_emailaddress"
    )
    return RedirectResponse(auth_url)

@router.get("/auth/linkedin/callback")
async def linkedin_callback(code: str, state: str):
    # Step 2: Exchange authorization code for access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
    }
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token")
    
    access_token = response.json().get("access_token")
    token_store["linkedin_token"] = access_token  # Store token
    
    # Step 3: Get user profile
    profile = await get_linkedin_profile(access_token)
    user_store["current_user"] = profile
    
    return {"access_token": access_token, "profile": profile}

async def get_linkedin_profile(access_token: str):
    profile_url = "https://api.linkedin.com/v2/me"
    email_url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    profile_response = requests.get(profile_url, headers=headers)
    email_response = requests.get(email_url, headers=headers)
    
    if profile_response.status_code != 200 or email_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get profile data")
    
    profile_data = profile_response.json()
    email_data = email_response.json()
    
    return {
        "name": f"{profile_data.get('localizedFirstName', '')} {profile_data.get('localizedLastName', '')}",
        "email": email_data.get("elements", [{}])[0].get("handle~", {}).get("emailAddress", ""),
        "profile_picture": None  # LinkedIn API v2 doesn't provide this directly
    }