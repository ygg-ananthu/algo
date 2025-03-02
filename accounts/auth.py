import requests

class UpstoxAuth:
    AUTH_URL = "https://api-v2.upstox.com/login/authorization/token"
    
    def __init__(self, user):
        self.client_id = user.client_id
        self.client_secret = user.client_secret
        self.code = user.code
        self.redirect_uri = 'http://127.0.0.1:8000/accounts/balance/'
        self.user = user
        
    def get_access_token(self):
        if not self.user.is_token_expired():
            print("848484940-4-4-4-4-4-4-4-4")
            return self.user.access_token
        print("0-0-0-9-9-9-0-0-0-0-0-0-")
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": self.code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
            }

        response = requests.post(url=self.AUTH_URL,headers=headers, data=payload)
        
        if response.status_code == 200:
            new_access_token = response.json().get("access_token")
            self.user.update_access_token(new_access_token)
            self.user.access_token = response.json().get("access_token")
            self.user.save()
            return response.json().get("access_token")
        else:
            return None


