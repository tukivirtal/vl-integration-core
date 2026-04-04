import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from supabase import create_client

app = Flask(__name__)

def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key: return None
    try: return create_client(url, key)
    except: return None

# ==========================================
# ENRUTADOR MAESTRO (Atrapa todas las rutas)
# ==========================================
@app.route('/', defaults={'path': ''}, methods=['POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['POST', 'OPTIONS'])
def enrutador(path):
    # 1. Manejo de la solicitud "pre-flight" de seguridad del navegador
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    # 2. Procesamiento de la petición real
    ruta_solicitada = request.path
    
    # Busca la palabra clave en la URL sin importar cómo la envíe Vercel
    if 'registro' in ruta_solicitada: return registro()
    if 'login' in ruta_solicitada: return login()
    if 'obtener_datos' in ruta_solicitada: return obtener_datos()
    
    return jsonify({"status": "error", "message": "Ruta no encontrada"}), 404

# ==========================================
# LÓGICA DE LAS FUNCIONES
# ==========================================
def registro():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email, password = data.get('email'), data.get('password')
    
    try:
        res = supabase.table('usuarios_refugio').select('email').eq('email', email).execute()
        if len(res.data) > 0: return jsonify({"status": "existe", "message": "Este correo ya tiene un refugio."}), 200
        
        pass_hash = generate_password_hash(password)
        nuevo_usuario = {
            "nombre": data.get('nombre'), "email": email, "contrasena": pass_hash,
            "fecha_nacimiento": data.get('fecha'), "hora_nacimiento": data.get('hora'),
            "ciudad": data.get('ciudad', '').upper(), "nivel_suscripcion": "free",
            "datos_natales": {"geo": {"lat": float(data.get('lat', 0)), "lon": float(data.get('lon', 0))}, "auth": "PENDING"}
        }
        supabase.table('usuarios_refugio').insert(nuevo_usuario).execute()
        return jsonify({"status": "exito"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def login():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email, password = data.get('email'), data.get('password')
    
    try:
        res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
        if len(res.data) == 0: return jsonify({"status": "error", "message": "No encontramos este correo en el Refugio."}), 404
        
        usuario = res.data[0]
        hash_guardado = usuario.get('contrasena')
        
        if check_password_hash(hash_guardado, password):
            return jsonify({"status": "exito", "datos": {"nombre": usuario.get('nombre'), "email": usuario.get('email')}}), 200
        return jsonify({"status": "error", "message": "Contraseña incorrecta."}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def obtener_datos():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    if not email: return jsonify({"status": "error", "message": "Falta correo"}), 400
    
    try:
        res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
        if len(res.data) > 0:
            u = res.data[0]
            return jsonify({
                "status": "exito", 
                "datos": {"nombre": u.get('nombre', 'Exploradora'), "ciudad": u.get('ciudad', 'Tu ciudad'), "fecha": u.get('fecha_nacimiento', '--/--/----')}
            }), 200
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
