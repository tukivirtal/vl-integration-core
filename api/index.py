import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from supabase import create_client
import datetime
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
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    ruta_solicitada = request.path
    # ... resto del código
    
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
    
    # --- LÓGICA DE PSICOLOGÍA DIARIA ---
    mensajes_diarios = [
        "Hoy el cielo te pide pausa. No tienes que resolverlo todo en las próximas 24 horas.",
        "Tu energía está en expansión. Es un gran momento para esa conversación que vienes postergando.",
        "La Luna sugiere introspección. Tu refugio hoy es tu propio silencio.",
        "Hay una alineación que favorece tu creatividad. Permítete jugar un poco más hoy.",
        "Momento de poner límites sanos. Decir 'no' a otros es decirte 'sí' a ti misma.",
        "La claridad llega tras la calma. Respira, los datos de tu mapa indican que el caos es temporal.",
        "Hoy tu intuición está afilada. Confía en ese primer pensamiento que tuviste al despertar."
    ]
    # Elegimos un mensaje basado en el día de la semana (0-6)
    dia_semana = datetime.datetime.now().weekday()
    mensaje_hoy = mensajes_diarios[dia_semana]
    # ----------------------------------

    try:
        res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
        if len(res.data) > 0:
            u = res.data[0]
            return jsonify({
                "status": "exito", 
                "datos": {
                    "nombre": u.get('nombre', 'Exploradora'), 
                    "ciudad": u.get('ciudad', 'Tu ciudad'), 
                    "fecha": u.get('fecha_nacimiento', '--/--/----'),
                    "mensaje_del_dia": mensaje_hoy  # <--- Enviamos el mensaje aquí
                }
            }), 200
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
