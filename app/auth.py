from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import requests
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus, unquote
import uuid
from redis import Redis

load_dotenv()
router = APIRouter()

active_states = set()

# In-memory storage (replace with database in production)
user_store = {}
token_store = {}

# Update environment variable names to match LinkedIn's standard
LINKEDIN_CLIENT_ID = os.getenv("CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/auth/linkedin/callback"

redis_client = Redis(host='localhost', port=6379, db=0)

@router.get("/linkedin")
async def linkedin_auth():
    if not LINKEDIN_CLIENT_ID:
        raise HTTPException(status_code=500, detail="LINKEDIN_CLIENT_ID not found in environment variables")
    if not LINKEDIN_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="LINKEDIN_CLIENT_SECRET not found in environment variables")

    csrf_token = str(uuid.uuid4())
    active_states.add(csrf_token)

    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={quote_plus(REDIRECT_URI)}"
        f"&state={csrf_token}"
        f"&scope=profile%20email"
    )

    return RedirectResponse(auth_url)

@router.get("/linkedin/callback")
async def linkedin_callback(request: Request):
    """
    Handle the callback from LinkedIn OAuth.
    """
    # Debug: Print all query parameters
    print("\nCallback Debug Information:")
    query_params = dict(request.query_params)
    print("All query parameters received:", query_params)
    
    # Check for error parameters that LinkedIn might send
    error = query_params.get('error')
    error_description = query_params.get('error_description')
    
    if error or error_description:
        error_msg = f"LinkedIn Error: {error}"
        if error_description:
            error_msg += f"\nDescription: {unquote(error_description)}"
        print(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    # Get code and state from query params
    code = query_params.get('code')
    state = query_params.get('state')

    print(f"\nReceived code: {code}")
    print(f"Received state: {state}")
    print(f"Active states: {active_states}")

    if not code:
        raise HTTPException(
            status_code=400, 
            detail=f"Authorization code not provided. Received parameters: {query_params}"
        )
    if not state:
        raise HTTPException(
            status_code=400, 
            detail=f"State parameter missing. Received parameters: {query_params}"
        )
    if state not in active_states:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid state parameter. Received state: {state}. Active states: {active_states}"
        )
    active_states.remove(state)

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
    }
    
    try:
        response = requests.post(
            token_url, 
            data=data, 
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            error_detail = f"Failed to get access token. Status: {response.status_code}, Response: {response.text}"
            print(f"Error: {error_detail}")
            raise HTTPException(status_code=400, detail=error_detail)
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")
        refresh_token = token_data.get("refresh_token")
        refresh_token_expires_in = token_data.get("refresh_token_expires_in")
        scope = token_data.get("scope")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token in response")
        
        profile_url = "https://api.linkedin.com/v2/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = requests.get(profile_url, headers=headers)
        
        return {
            "access_token": access_token,
            "expires_in": expires_in,
            "refresh_token": refresh_token,
            "refresh_token_expires_in": refresh_token_expires_in,
            "scope": scope,
            "profile": profile_response.json() if profile_response.status_code == 200 else None
        }
    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Request failed: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")