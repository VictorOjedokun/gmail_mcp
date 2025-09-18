from google_auth_oauthlib.flow import Flow
import urllib

# Set up the flow
flow = Flow.from_client_config(
    {
        "web": {
            "client_id": "YOUR-CLIENT-ID",
            "client_secret": "YOUR-CLIENT-SECRET",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=[
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.labels",
    ],
)
flow.redirect_uri = "http://localhost:8080/auth/callback"

# Get authorization URL
auth_url, _ = flow.authorization_url(access_type="offline")
print(f"Go to: {auth_url}")
import urllib.parse

while True:
    redirect_response = input("Enter the full redirect URL: ")
    code = redirect_response.split("code=")[1].split("&")[0]
    code = urllib.parse.unquote(code)
    print(f"Authorization code: {code}")
    try:
        flow.fetch_token(code=code)
        break
    except Exception as e:
        print("Error fetching token:", e)

credentials = flow.credentials
print(credentials.to_json())
