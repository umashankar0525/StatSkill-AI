#!/usr/bin/env python3
"""
StatSkill AI - Backend Server
Provides REST API endpoints and serves the frontend Single Page Application.
Built for the Ministry of Statistics and Programme Implementation (MoSPI) & National Statistical System.
"""

import http.server
import json
import urllib.parse
import os
import time
import random
import hashlib
import secrets
import sqlite3
import re
def load_env_file():
    """Loads environment variables from .env file if it exists."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
            print(f"[Config] Loaded environment variables from .env file.")
        except Exception as e:
            print(f"[Config Warning] Could not parse .env: {e}")

load_env_file()

import live_api
import storage

PORT = int(os.environ.get("STATSKILL_PORT", "8000"))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(DIRECTORY, "static")

# Organization seed data for new databases
DB_PATH = storage.DB_PATH
SCHEMA_PATH = os.path.join(DIRECTORY, "db", "schema.sql")
SEED_PATH = os.path.join(DIRECTORY, "db", "seed.sql")

# In-Memory & Persistent Storage
USERS_FILE = os.environ.get("STATSKILL_USERS", os.path.join(DIRECTORY, "users.json"))
USERS = {} # email -> user record
OTP_STORE = {} # email -> {"otp": "123456", "expires": timestamp, "ministry": ministry}
VERIFIED_EMAILS = set()

def load_users():
    global USERS
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                USERS = json.load(f)
            print(f"[Users Store] Loaded {len(USERS)} registered users from users.json")
        except Exception as e:
            print(f"[Users Store Warning] Could not read users.json: {e}")
            USERS = {}
    else:
        USERS = {}

def save_users():
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(USERS, f, indent=2)
        print(f"[Users Store] Persisted {len(USERS)} users to users.json")
    except Exception as e:
        print(f"[Users Store Warning] Could not write users.json: {e}")

load_users()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hashed = 'pbkdf2$' + hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 300000).hex()
    return hashed, salt

def verify_password(password, salt, stored):
    if stored.startswith('pbkdf2$'):
        expected = hash_password(password, salt)[0]
    else:
        expected = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return secrets.compare_digest(expected, stored)

def send_real_sms_otp(mobile, otp):
    """
    Sends real SMS OTP to Indian mobile numbers (+91) using configured SMS gateway.
    Supports Fast2SMS, 2Factor.in, and Twilio.
    """
    import urllib.request
    import urllib.parse
    import base64

    clean_mobile = re.sub(r'\D', '', str(mobile))
    if len(clean_mobile) == 12 and clean_mobile.startswith('91'):
        clean_mobile = clean_mobile[2:]

    fast2sms_key = os.environ.get("FAST2SMS_API_KEY")
    twofactor_key = os.environ.get("TWO_FACTOR_API_KEY") or os.environ.get("TWOFACTOR_API_KEY")
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_from = os.environ.get("TWILIO_FROM_NUMBER")

    # 1. Fast2SMS (India Quick OTP Gateway)
    if fast2sms_key:
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {
                "authorization": fast2sms_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = urllib.parse.urlencode({
                "variables_values": otp,
                "route": "otp",
                "numbers": clean_mobile
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                print(f"[Fast2SMS Gateway] Real SMS dispatched to +91-{clean_mobile}: {result}")
                return True, "SMS dispatched via Fast2SMS"
        except Exception as e:
            print(f"[Fast2SMS Error] Failed to send SMS: {e}")

    # 2. 2Factor.in (India OTP Gateway)
    if twofactor_key:
        try:
            url = f"https://2factor.in/v1/API/V1/{twofactor_key}/SMS/{clean_mobile}/{otp}/AUTOGEN"
            req = urllib.request.Request(url, headers={"User-Agent": "StatSkill-AI/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                print(f"[2Factor.in Gateway] Real SMS dispatched to +91-{clean_mobile}: {result}")
                return True, "SMS dispatched via 2Factor"
        except Exception as e:
            print(f"[2Factor Error] Failed to send SMS: {e}")

    # 3. Twilio SMS
    if twilio_sid and twilio_token and twilio_from:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            auth_str = f"{twilio_sid}:{twilio_token}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            headers = {
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = urllib.parse.urlencode({
                "To": f"+91{clean_mobile}",
                "From": twilio_from,
                "Body": f"Your StatSkill AI (MoSPI) verification OTP code is: {otp}. Valid for 5 minutes."
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                print(f"[Twilio Gateway] Real SMS dispatched to +91-{clean_mobile}: SID {result.get('sid')}")
                return True, "SMS dispatched via Twilio"
        except Exception as e:
            print(f"[Twilio Error] Failed to send SMS: {e}")

    # Fallback / Dev info when no SMS Gateway API Key is provided
    print("\n" + "="*70)
    print(f"📡 [SMS GATEWAY DISPATCH NOTICE]")
    print(f"👉 Target Indian Mobile: +91 {clean_mobile}")
    print(f"👉 6-Digit OTP Code: [{otp}]")
    print(f"ℹ️  To deliver real SMS directly to mobile handsets over telecom networks,")
    print(f"   add your FAST2SMS_API_KEY or TWO_FACTOR_API_KEY or TWILIO credentials in .env")
    print("="*70 + "\n")
    return False, "SMS Gateway credentials not yet configured in .env"

def send_smtp_otp(to_email, otp):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print(f"\n=======================================================")
        print(f"[DEV MODE] SMTP not configured. OTP for {to_email}: {otp}")
        print(f"=======================================================\n")
        return False

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = "StatSkill AI — Email Verification OTP"

        body = f"Your StatSkill AI verification code is: {otp}\nThis OTP is valid for 5 minutes."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"[SMTP] Successfully sent OTP to {to_email}")
        return True
    except Exception as e:
        print(f"[SMTP Error] Failed to send email via SMTP: {e}")
        print(f"[DEV MODE FALLBACK] OTP for {to_email}: {otp}")
        return False

def init_db_if_needed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ministries'")
    row = cursor.fetchone()
    if not row:
        print("[Attached DB] Initializing igot_demo.db from schema.sql and seed.sql...")
        if os.path.exists(SCHEMA_PATH) and os.path.exists(SEED_PATH):
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                cursor.executescript(f.read())
            with open(SEED_PATH, 'r', encoding='utf-8') as f:
                cursor.executescript(f.read())
            print("[Attached DB] igot_demo.db successfully seeded with Ministries & State Departments!")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(users)")
        cols = [r["name"] for r in cursor.fetchall()]
        if "role" not in cols:
            print("[Attached DB] Updating users table schema...")
            raise RuntimeError("Legacy users schema requires a reviewed migration; no data was removed.")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            salt TEXT,
            role TEXT DEFAULT 'learner',
            employee_id TEXT,
            org_type TEXT,
            ministry_id TEXT,
            state TEXT,
            department TEXT,
            organisation TEXT,
            designation TEXT,
            overall_score INTEGER DEFAULT 0,
            learning_hours REAL DEFAULT 0,
            assessments_completed INTEGER DEFAULT 0,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP
        );
    """)

    # Check and add last_login_at if table already existed
    cursor.execute("PRAGMA table_info(users)")
    cols = [r["name"] for r in cursor.fetchall()]
    if "mobile" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN mobile TEXT")
    if "last_login_at" not in cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP")
            conn.commit()
        except Exception:
            pass

    # Login audit logs table for full compliance and tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            email TEXT,
            name TEXT,
            ip_address TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'SUCCESS'
        );
    """)
    conn.commit()
    conn.close()

try:
    init_db_if_needed()
except Exception as err:
    print(f"[Attached DB Warning] Error initializing DB: {err}")

live_api.init()

class StatSkillHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path.startswith("/api/") and live_api.handle(self, "GET", path, query):
            return

        # REST API Router
        if path.startswith("/api/"):
            self.handle_api_get(path, query)
            return

        # Serve static files or fallback to index.html for SPA
        if not os.path.exists(os.path.join(STATIC_DIR, path.lstrip('/'))) or path == '/':
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            content_length = int(self.headers.get('Content-Length', 0))
        except ValueError:
            self.send_json({"success": False, "error": "Invalid request length"}, 400)
            return
        if not 0 <= content_length <= 36 * 1024 * 1024:
            self.send_json({"success": False, "error": "Request exceeds 36 MB"}, 413)
            return
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
        try:
            body = json.loads(post_data)
        except Exception:
            self.send_json({"success": False, "error": "Invalid JSON"}, 400)
            return
        if not isinstance(body, dict):
            self.send_json({"success": False, "error": "Expected a JSON object"}, 400)
            return
        if live_api.handle(self, "POST", path, body):
            return

        if path.startswith("/api/"):
            self.handle_api_post(path, body)
            return

        self.send_error(404, "Endpoint not found")

    def send_json(self, data, status_code=200):
        if isinstance(data, dict) and data.get("token") and data.get("user"):
            data["user"] = live_api.bind_session(data["token"], data["user"])
            data["role"] = data["user"]["role"]
            if "officer" in data:
                data["officer"] = data["user"]
        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def handle_api_get(self, path, query):
        if path == "/api/states":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT state FROM state_departments ORDER BY state")
            rows = cursor.fetchall()
            conn.close()
            self.send_json([r["state"] for r in rows])
        elif path == "/api/ministries/central":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM ministries WHERE parent_ministry IS NULL ORDER BY name")
            rows = cursor.fetchall()
            conn.close()
            self.send_json([{"id": r["id"], "name": r["name"]} for r in rows])
        elif path.startswith("/api/ministries/central/") and path.endswith("/departments"):
            parts = [p for p in path.split('/') if p]
            if len(parts) >= 5 and parts[4] == 'departments':
                ministry_id = parts[3]
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM ministries WHERE parent_ministry = ? ORDER BY name", (ministry_id,))
                rows = cursor.fetchall()
                conn.close()
                self.send_json([{"id": r["id"], "name": r["name"]} for r in rows])
            else:
                self.send_json({"error": "Invalid URL format"}, status_code=400)
        elif path.startswith("/api/departments/state/"):
            state_encoded = path[len("/api/departments/state/"):]
            state_name = urllib.parse.unquote(state_encoded)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM state_departments WHERE state = ? AND parent_ministry IS NULL ORDER BY name", (state_name,))
            rows = cursor.fetchall()
            conn.close()
            self.send_json([{"id": r["id"], "name": r["name"]} for r in rows])
        else:
            self.send_json({"error": "Unknown API GET endpoint", "path": path}, status_code=404)

    def handle_api_post(self, path, body):

        # -------------------------------------------------------------
        # ROUTE 1: POST /api/auth/send-otp
        # -------------------------------------------------------------
        if path == "/api/auth/send-otp":
            mobile = (body.get("mobile") or "").strip()
            mobile_clean = re.sub(r"\D", "", mobile)
            email = (body.get("email") or "").lower().strip()
            ministry = (body.get("ministry") or "").strip()

            identifier = None
            channel = "email"

            if mobile_clean and len(mobile_clean) == 10 and re.match(r"^[6-9]\d{9}$", mobile_clean):
                identifier = mobile_clean
                channel = "sms"
            elif email and re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
                identifier = email
                channel = "email"
            else:
                self.send_json({"success": False, "error": "Please enter a valid 10-digit mobile number (e.g. 9876543210) or official email"}, status_code=400)
                return

            if not ministry or ministry == "-- Select Ministry or Department --":
                self.send_json({"success": False, "error": "Please select a Ministry or Department"}, status_code=400)
                return

            # Check if mobile or email is already registered in USERS cache or SQLite
            is_already_registered = False
            if identifier in USERS:
                is_already_registered = True
            else:
                for u in USERS.values():
                    if u.get("mobile") == mobile_clean or (email and u.get("email") == email):
                        is_already_registered = True
                        break

            if not is_already_registered:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ? OR mobile = ?", (email if email else identifier, mobile_clean if mobile_clean else identifier))
                    if cursor.fetchone():
                        is_already_registered = True
                    conn.close()
                except Exception:
                    pass

            if is_already_registered:
                self.send_json({
                    "success": False,
                    "alreadyRegistered": True,
                    "error": f"The {'mobile number +91 ' + mobile_clean if channel == 'sms' else 'email ' + email} is already registered. Please log in with your credentials."
                }, status_code=400)
                return

            # Generate brand new 6-digit OTP code
            otp = f"{random.randint(100000, 999999)}"
            OTP_STORE[identifier] = {
                "otp": otp,
                "expires": time.time() + 300,
                "ministry": ministry,
                "mobile": mobile_clean,
                "email": email,
                "channel": channel
            }

            if channel == "email" and email:
                sent_real = send_smtp_otp(email, otp)
            else:
                sent_real, msg = send_real_sms_otp(mobile_clean, otp)
                if not sent_real:
                    print(f"[SMS DEV NOTICE] >>> Real SMS delivery requires SMS gateway API key. Demo OTP [{otp}] generated for +91-{mobile_clean} <<<")

            self.send_json({
                "success": True,
                "message": ("Verification code delivered." if sent_real else "Local demo verification: delivery gateway unavailable; no message was sent."),
                "otp": None if sent_real else otp,
                "demo_mode": not sent_real,
                "identifier": identifier,
                "mobile": mobile_clean,
                "email": email,
                "channel": channel
            })
            return

        # -------------------------------------------------------------
        # ROUTE 2: POST /api/auth/verify-otp
        # -------------------------------------------------------------
        elif path == "/api/auth/verify-otp":
            identifier = (body.get("identifier") or body.get("mobile") or body.get("email") or "").lower().strip()
            if not identifier:
                identifier = (body.get("email") or "").lower().strip()
            identifier_clean = re.sub(r"\D", "", identifier) if re.match(r"^\d{10}$", identifier) else identifier

            otp = str(body.get("otp") or "").strip()

            if not identifier or not otp:
                self.send_json({"success": False, "error": "Mobile/Email identifier and 6-digit OTP are required"}, status_code=400)
                return

            record = OTP_STORE.get(identifier) or OTP_STORE.get(identifier_clean)
            if not record:
                # Also search values
                for k, v in OTP_STORE.items():
                    if v.get("mobile") == identifier_clean or v.get("email") == identifier:
                        record = v
                        identifier = k
                        break

            if not record or record["otp"] != otp or time.time() > record["expires"]:
                self.send_json({"success": False, "error": "Invalid OTP code entered. Please re-enter the code or request a new OTP."}, status_code=400)
                return

            VERIFIED_EMAILS.add(identifier)
            if record.get("mobile"):
                VERIFIED_EMAILS.add(record["mobile"])
            if record.get("email"):
                VERIFIED_EMAILS.add(record["email"])

            if identifier in OTP_STORE:
                del OTP_STORE[identifier]

            self.send_json({"success": True, "message": "OTP verification successful"})
            return

        # -------------------------------------------------------------
        # ROUTE 3: POST /api/auth/register
        # -------------------------------------------------------------
        elif path in ["/api/auth/register", "/api/register"]:
            email = (body.get("email") or "").lower().strip()
            mobile = re.sub(r"\D", "", str(body.get("mobile") or ""))
            name = (body.get("name") or "").strip()
            ministry = (body.get("ministry") or "Ministry of Statistics & Programme Implementation (MoSPI)").strip()
            department = (body.get("department") or ministry).strip()
            designation = (body.get("designation") or "Senior Statistical Officer (SSO)").strip()
            org_type = (body.get("gov_type") or body.get("org_type") or "Central Government").strip()
            password = body.get("password") or ""

            try:
                work_profile = live_api.registration_profile(body)
            except live_api.APIError as error:
                self.send_json({"success": False, "error": str(error)}, status_code=error.status)
                return

            if not email and mobile:
                email = f"{mobile}@nic.gov.in"

            if not email:
                self.send_json({"success": False, "error": "Email address or 10-digit mobile number is required"}, status_code=400)
                return

            if email not in VERIFIED_EMAILS and mobile not in VERIFIED_EMAILS:
                self.send_json({"success": False, "error": "Mobile or Email verification via OTP is required before registration"}, status_code=400)
                return

            if email in USERS:
                self.send_json({"success": False, "error": "An account with this email/mobile is already registered. Please log in."}, status_code=400)
                return

            # Password Strength Validation: min 8 chars, 1 letter, 1 number
            if len(password) < 8 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):
                self.send_json({"success": False, "error": "Password must be at least 8 characters long and contain both letters and numbers"}, status_code=400)
                return

            # Auto-generate Official ID format {CADRE}/{YEAR}/{5-digit-number}
            year = time.strftime("%Y")
            num_hash = (int(hashlib.sha256(email.encode('utf-8')).hexdigest()[:8], 16) % 90000) + 10000
            cadre = "ISS" if ("mospi" in ministry.lower() or "central" in ministry.lower() or "statistical" in ministry.lower()) else "SSS"
            official_id = f"{cadre}/{year}/{num_hash}"

            hashed, salt = hash_password(password)
            user_name = name if name else email.split('@')[0].replace('.', ' ').replace('_', ' ').title()

            user_record = {
                "id": f"usr_{secrets.token_hex(6)}",
                "email": email,
                "mobile": mobile,
                "name": user_name,
                "ministry": ministry,
                "department": department,
                "designation": designation,
                "role": designation,
                "employeeId": official_id,
                "org_type": org_type,
                "password_hash": hashed,
                "salt": salt,
                "overallScore": 0,
                "learningHours": 0,
                "registered_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            USERS[email] = user_record

            # Also persist into SQLite users table for system compatibility
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users
                    (name, email, mobile, password_hash, salt, role, employee_id, org_type, ministry_id, department, organisation, designation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_name, email, mobile, hashed, salt, "learner", official_id, org_type, ministry, department, "org_sdrd", designation))
                if work_profile is not None:
                    cursor.execute('INSERT INTO learner_profiles(user_id,data) VALUES(?,?)',
                                   (str(cursor.lastrowid), json.dumps(work_profile, ensure_ascii=False)))
                conn.commit()
                conn.close()
                print(f"[DB Success] Registered new user '{user_name}' ({email}, mobile: {mobile}) into SQLite.")
            except Exception as e:
                USERS.pop(email, None)
                self.send_json({"success": False, "error": "Registration could not be saved. Please retry."}, 500)
                return
            save_users()

            safe_user = {k: v for k, v in user_record.items() if k not in ["password_hash", "salt"]}
            token = f"token_registered_{secrets.token_hex(8)}"
            self.send_json({"success": True, "token": token, "user": safe_user, "officer": safe_user})
            return

        # -------------------------------------------------------------
        # ROUTE 4: POST /api/auth/login-send-otp (Login Step 1: Send OTP)
        # -------------------------------------------------------------
        elif path == "/api/auth/login-send-otp":
            identifier = (body.get("email") or body.get("identifier") or body.get("mobile") or "").lower().strip()
            identifier_clean = re.sub(r"\D", "", identifier)
            password = body.get("password") or ""
            is_passwordless = body.get("passwordless", False)

            user = USERS.get(identifier)
            if not user and identifier_clean and len(identifier_clean) == 10:
                for u in USERS.values():
                    if u.get("mobile") == identifier_clean:
                        user = u
                        break

            # Fallback check against SQLite users table
            if not user:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ? OR mobile = ?", (identifier, identifier_clean if len(identifier_clean) == 10 else identifier))
                    row = cursor.fetchone()
                    conn.close()
                    if row:
                        u = dict(row)
                        user = {
                            "id": str(u["id"]),
                            "email": u["email"],
                            "mobile": u.get("mobile") or "",
                            "name": u["name"],
                            "ministry": u.get("ministry_id") or "Ministry of Statistics & Programme Implementation",
                            "department": u.get("department") or "National Statistical Office (NSO)",
                            "designation": u.get("designation") or "Senior Statistical Officer (SSO)",
                            "role": u.get("designation") or "Senior Statistical Officer (SSO)",
                            "employeeId": u.get("employee_id") or "ISS/2026/84920",
                            "password_hash": u.get("password_hash"),
                            "salt": u.get("salt"),
                            "overallScore": u.get("overall_score") or 0,
                            "learningHours": u.get("learning_hours") or 0
                        }
                except Exception:
                    pass

            if not user:
                self.send_json({"success": False, "error": "Account not found with this mobile number or email. Please register first."}, status_code=404)
                return

            if not is_passwordless:
                if not user.get("password_hash") or not user.get("salt"):
                    self.send_json({"success": False, "error": "Invalid login credentials. Please try again."}, status_code=401)
                    return
                if not verify_password(password, user["salt"], user["password_hash"]):
                    self.send_json({"success": False, "error": "Invalid password entered. Please try again."}, status_code=401)
                    return

            # Generate 6-digit Login OTP
            otp = f"{random.randint(100000, 999999)}"
            login_key = f"login_{identifier}"
            OTP_STORE[login_key] = {
                "otp": otp,
                "expires": time.time() + 300,
                "user": user,
                "identifier": identifier
            }

            mobile_target = user.get("mobile") or identifier_clean
            email_target = user.get("email") or identifier

            sent_real = False
            if mobile_target and len(mobile_target) == 10:
                sent_real, msg = send_real_sms_otp(mobile_target, otp)
                if not sent_real:
                    print(f"[LOGIN SMS DEV NOTICE] >>> Real SMS delivery requires SMS gateway API key. Demo Login OTP [{otp}] generated for +91-{mobile_target} <<<")
            elif email_target and "@" in email_target:
                sent_real = send_smtp_otp(email_target, otp)

            self.send_json({
                "success": True,
                "message": "Login code delivered." if sent_real else "Local demo login verification; no message was sent.",
                "otp": None if sent_real else otp,
                "demo_mode": not sent_real,
                "identifier": identifier,
                "mobile": mobile_target,
                "email": email_target
            })
            return

        # -------------------------------------------------------------
        # ROUTE 5: POST /api/auth/login-verify-otp (Login Step 2: Verify OTP)
        # -------------------------------------------------------------
        elif path == "/api/auth/login-verify-otp":
            identifier = (body.get("identifier") or body.get("mobile") or body.get("email") or "").lower().strip()
            otp_entered = str(body.get("otp", "")).strip()

            login_key = f"login_{identifier}"
            record = OTP_STORE.get(login_key)

            if not record:
                # Try finding by mobile clean
                clean_id = re.sub(r"\D", "", identifier)
                for k, v in list(OTP_STORE.items()):
                    if k.startswith("login_") and (v.get("identifier") == clean_id or v.get("user", {}).get("mobile") == clean_id):
                        record = v
                        login_key = k
                        break

            if not record:
                self.send_json({"success": False, "error": "No active login session found. Please request a new OTP code."}, status_code=400)
                return

            if time.time() > record["expires"]:
                del OTP_STORE[login_key]
                self.send_json({"success": False, "error": "Login OTP has expired. Please request a new code."}, status_code=400)
                return

            if record["otp"] != otp_entered:
                self.send_json({"success": False, "error": "Invalid OTP code entered. Please re-enter the code or request a new OTP."}, status_code=400)
                return

            # Success -> Issue Token
            user = record["user"]
            del OTP_STORE[login_key]

            safe_user = {k: v for k, v in user.items() if k not in ["password_hash", "salt"]}
            token = f"token_login_{secrets.token_hex(8)}"

            # Audit log to SQLite
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ? OR LOWER(email) = ?", (safe_user.get("id"), safe_user.get("email")))
                ip_addr = self.client_address[0] if hasattr(self, 'client_address') and self.client_address else '127.0.0.1'
                cursor.execute("""
                    INSERT INTO login_audit_logs (user_id, email, name, ip_address, login_time, status)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'SUCCESS')
                """, (safe_user.get("id") or safe_user.get("employeeId"), safe_user.get("email"), safe_user.get("name"), ip_addr))
                conn.commit()
                conn.close()
                print(f"[DB Audit] Recorded successful OTP login for '{safe_user.get('name')}' into SQLite database.")
            except Exception as e:
                print(f"[DB Warning] Could not log login event to SQLite: {e}")

            self.send_json({"success": True, "token": token, "user": safe_user, "role": safe_user.get("role", "learner")})
            return

        # -------------------------------------------------------------
        # ROUTE 6: POST /api/auth/login (Direct Credential Auth)
        # -------------------------------------------------------------
        elif path == "/api/auth/login":
            identifier = (body.get("username") or body.get("email") or body.get("identifier") or body.get("mobile") or "").lower().strip()
            identifier = live_api.account_service.login_identifier(identifier)
            identifier_clean = re.sub(r"\D", "", identifier)
            password = body.get("password") or ""

            user = USERS.get(identifier)

            if not user and identifier_clean and len(identifier_clean) == 10:
                for u in USERS.values():
                    if u.get("mobile") == identifier_clean:
                        user = u
                        break

            # Fallback check against SQLite users table
            if not user:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ? OR mobile = ?", (identifier, identifier_clean if len(identifier_clean) == 10 else identifier))
                    row = cursor.fetchone()
                    conn.close()
                    if row:
                        u = dict(row)
                        user = {
                            "id": str(u["id"]),
                            "email": u["email"],
                            "mobile": u.get("mobile") or "",
                            "name": u["name"],
                            "ministry": u.get("ministry_id") or "Ministry of Statistics & Programme Implementation",
                            "department": u.get("department") or "National Statistical Office (NSO)",
                            "designation": u.get("designation") or "Senior Statistical Officer (SSO)",
                            "role": u.get("designation") or "Senior Statistical Officer (SSO)",
                            "employeeId": u.get("employee_id") or "ISS/2026/84920",
                            "password_hash": u.get("password_hash"),
                            "salt": u.get("salt"),
                            "overallScore": u.get("overall_score") or 0,
                            "learningHours": u.get("learning_hours") or 0
                        }
                except Exception:
                    pass

            if not user or not user.get("password_hash") or not user.get("salt"):
                self.send_json({"success": False, "error": "Invalid mobile/email or password"}, status_code=401)
                return

            if not verify_password(password, user["salt"], user["password_hash"]):
                self.send_json({"success": False, "error": "Invalid mobile/email or password"}, status_code=401)
                return

            safe_user = {k: v for k, v in user.items() if k not in ["password_hash", "salt"]}
            token = f"token_login_{secrets.token_hex(8)}"

            # Persist login timestamp & audit entry into SQLite database
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ? OR LOWER(email) = ?", (safe_user.get("id"), safe_user.get("email")))
                ip_addr = self.client_address[0] if hasattr(self, 'client_address') and self.client_address else '127.0.0.1'
                cursor.execute("""
                    INSERT INTO login_audit_logs (user_id, email, name, ip_address, login_time, status)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'SUCCESS')
                """, (safe_user.get("id") or safe_user.get("employeeId"), safe_user.get("email"), safe_user.get("name"), ip_addr))
                conn.commit()
                conn.close()
                print(f"[DB Audit] Recorded direct login for '{safe_user.get('name')}' into SQLite database.")
            except Exception as e:
                print(f"[DB Warning] Could not log login event to SQLite: {e}")

            self.send_json({"success": True, "token": token, "user": safe_user, "role": safe_user.get("role", "learner")})
            return

        else:
            self.send_json({"success": False, "error": "Unknown endpoint"}, 404)


def run_server():
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), StatSkillHandler) as httpd:
        print(f"=======================================================")
        print(f"StatSkill AI Server running at http://localhost:{PORT}")
        print(f"=======================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
