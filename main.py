import os
import secrets
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Add Session Middleware
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Set up OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.get('/')
async def homepage(request: Request):
    user = request.session.get('user')
    if user:
        name = user.get('name', 'User')
        email = user.get('email', 'Unknown Email')
        picture = user.get('picture')
        
        html = f"""
        <html>
            <head>
                <title>Google OAuth Login</title>
                <style>
                    body {{ font-family: sans-serif; padding: 2rem; text-align: center; }}
                    img {{ border-radius: 50%; margin-top: 10px; }}
                    .btn {{ padding: 10px 20px; background-color: #d9534f; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; display: inline-block; }}
                </style>
            </head>
            <body>
                <h1>Welcome, {name}!</h1>
                <p>Email: {email}</p>
                {f'<img src="{picture}" width="100" />' if picture else ''}
                <br>
                <a class="btn" href="/logout">Logout</a>
            </body>
        </html>
        """
        return HTMLResponse(html)
    else:
        html = """
        <html>
            <head>
                <title>Google OAuth Login</title>
                <style>
                    body { font-family: sans-serif; padding: 2rem; text-align: center; }
                    .btn { padding: 10px 20px; background-color: #4285F4; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; display: inline-block; }
                </style>
            </head>
            <body>
                <h1>Google OAuth Integration</h1>
                <p>You are not logged in.</p>
                <a class="btn" href="/login">Login with Google</a>
            </body>
        </html>
        """
        return HTMLResponse(html)

@app.get('/login')
async def login(request: Request):
    # This creates the redirect URL for Google to call back to
    # using the route name 'auth' defined below
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth/google/callback')
async def auth(request: Request):
    try:
        # Retrieve the access token and user information
        token = await oauth.google.authorize_access_token(request)
        user = token.get('userinfo')
        if user:
            # Store user data in the session
            request.session['user'] = dict(user)
    except Exception as e:
        print(f"Error during authentication: {e}")
    
    # Redirect to the homepage
    return RedirectResponse(url='/')

@app.get('/logout')
async def logout(request: Request):
    # Clear the session
    request.session.pop('user', None)
    return RedirectResponse(url='/')
