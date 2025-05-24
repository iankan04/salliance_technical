from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from app.auth import router as auth_router
import requests

app = FastAPI()

# Mount the auth router
app.include_router(auth_router, prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/linkedin")

@app.get("/")
async def root():
    """
    Base Case
    """
    return { "message": "Welcome to your server. Go to /auth/linkedin to start authentication" }

@app.get("/user")
async def get_user_profile(access_token: str = Depends(oauth2_scheme)):
    """
    Get LinkedIn user profile using the access token
    """
    try:
        # Basic profile information
        profile_url = "https://api.linkedin.com/v2/userinfo"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        profile_response = requests.get(profile_url, headers=headers)
        if profile_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get profile information: {profile_response.text}"
            )

        profile_data = profile_response.json()

        user_data = {
            "firstName": profile_data.get("given_name"),
            "lastName": profile_data.get("family_name"),
            "email": profile_data.get("email"),
            "picture": profile_data.get("picture")
        }

        return user_data

    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Request failed: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")