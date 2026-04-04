import os
import datetime
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
# ENRUTADOR MAESTRO CON SEGURIDAD TOTAL
# ==========================================
@app.route('/', defaults={'path': ''}, methods=['POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['POST', 'OPTIONS'])
def enrutador(path):
    # Seguridad de Navegador (CORS)
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    
    try:
        ruta_solicitada = request.path
        
        # Mapeo explícito de funciones
        if 'login' in ruta_solicitada:
            return login()
        if 'registro' in ruta_solicitada:
            return registro()
        if 'obtener_datos' in ruta_solicitada:
            return obtener_datos()
            
        return jsonify({"status": "error", "message": f"Ruta {ruta_solicitada} no encontrada"}), 404
        
    except Exception as e:
        # Esto evita el error de "Unexpected token <" mandando un JSON en lugar de un error 500 HTML
        return jsonify({"status": "error", "message": "Error interno: " + str(e)}), 500

# ==========================================
# FUNCIONES DE LÓGICA (Sincronizadas)
# ==========================================
def login():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Credenciales incompletas."}), 400
    
    res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
    if len(res.data) == 0:
        return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404
        
    usuario = res.data[0]
    if check_password_hash(usuario.get('contrasena'), password):
        return jsonify({
            "status": "exito", 
            "datos": {"nombre": usuario.get('nombre'), "email": usuario.get('email')}
        }), 200
        
    return jsonify({"status": "error", "message": "Contraseña incorrecta."}), 401

def obtener_datos():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    
    mensajes = [
        "Hoy el cielo te pide pausa. No tienes que resolverlo todo hoy.",
        "Tu energía está en expansión. Es un gran momento para avanzar.",
        "La Luna sugiere introspección. Tu refugio es tu silencio.",
        "Hay una alineación que favorece tu creatividad. Juega un poco.",
        "Momento de poner límites sanos. Decirte 'sí' a ti misma.",
        "La claridad llega tras la calma. El mapa indica paz.",
        "Hoy tu intuición está afilada. Confía en tu primer pensamiento."
    ]
    mensaje_hoy = mensajes[datetime.datetime.now().weekday()]

    res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
    if len(res.data) > 0:
        u = res.data[0]
        return jsonify({
            "status": "exito", 
            "datos": {
                "nombre": u.get('nombre', 'Exploradora'), 
                "ciudad": u.get('ciudad', 'Tu ciudad'), 
                "fecha": u.get('fecha_nacimiento', '--/--/----'),
                "mensaje_del_dia": mensaje_hoy
            }
        }), 200
    return jsonify({"status": "error", "message": "No se hallaron datos."}), 404

def registro():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email, password = data.get('email'), data.get('password')
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Faltan datos clave."}), 400
    
    try:
        res = supabase.table('usuarios_refugio').select('email').eq('email', email).execute()
        if len(res.data) > 0: return jsonify({"status": "existe", "message": "Correo ya registrado."}), 200
        
        pass_hash = generate_password_hash(password)
        
        # Filtro de seguridad para números (evita que Python se estrelle)
        lat_val = data.get('lat')
        lon_val = data.get('lon')
        lat = float(lat_val) if lat_val else 0.0
        lon = float(lon_val) if lon_val else 0.0
        
        nuevo_usuario = {
            "nombre": data.get('nombre'), "email": email, "contrasena": pass_hash,
            "fecha_nacimiento": data.get('fecha'), "hora_nacimiento": data.get('hora'),
            "ciudad": data.get('ciudad', '').upper(), "nivel_suscripcion": "free",
            "datos_natales": {"geo": {"lat": lat, "lon": lon}, "auth": "PENDING"}
        }
        supabase.table('usuarios_refugio').insert(nuevo_usuario).execute()
        return jsonify({"status": "exito"}), 201
    except Exception as e:
        print(f"Error en registro: {str(e)}", flush=True)
        return jsonify({"status": "error", "message": "Error interno al guardar."}), 500
