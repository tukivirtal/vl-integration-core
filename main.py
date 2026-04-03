import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key: return None
    try: return create_client(url, key)
    except: return None

# ==========================================
# 1. RUTA DE REGISTRO
# ==========================================
@app.route('/registro', methods=['POST'])
def registro():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Error de base de datos."}), 500
    data = request.json
    email, password = data.get('email'), data.get('password')
    
    try:
        respuesta_busqueda = supabase.table('usuarios_refugio').select('email').eq('email', email).execute()
        if len(respuesta_busqueda.data) > 0:
            return jsonify({"status": "existe", "message": "Este correo ya tiene un refugio."}), 200
        
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

# ==========================================
# 2. NUEVA RUTA DE LOGIN (ACCESO)
# ==========================================
@app.route('/login', methods=['POST'])
def login():
    supabase = get_supabase_client()
    data = request.json
    email, password = data.get('email'), data.get('password')

    try:
        res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
        if len(res.data) == 0:
            return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404
        
        usuario = res.data[0]
        # Verificamos si la contraseña coincide con el hash guardado
        if check_password_hash(usuario.get('contrasena'), password):
            return jsonify({
                "status": "exito",
                "datos": {"nombre": usuario.get('nombre'), "email": usuario.get('email')}
            }), 200
        else:
            return jsonify({"status": "error", "message": "Contraseña incorrecta."}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 3. RUTA PARA OBTENER DATOS
# ==========================================
@app.route('/obtener_datos', methods=['POST'])
def obtener_datos():
    supabase = get_supabase_client()
    email = request.json.get('email')
    try:
        res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
        if len(res.data) > 0:
            u = res.data[0]
            return jsonify({"status": "exito", "datos": {"nombre": u.get('nombre'), "ciudad": u.get('ciudad'), "fecha": u.get('fecha_nacimiento')}}), 200
        return jsonify({"status": "error"}), 404
    except: return jsonify({"status": "error"}), 500
