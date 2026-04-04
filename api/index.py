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

@app.route('/', defaults={'path': ''}, methods=['POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['POST', 'OPTIONS'])
def enrutador(path):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    ruta_solicitada = request.path
    if 'registro' in ruta_solicitada: return registro()
    if 'login' in ruta_solicitada: return login()
    if 'obtener_datos' in ruta_solicitada: return obtener_datos()
    
    return jsonify({"status": "error", "message": "Ruta no encontrada"}), 404

def obtener_datos():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    if not email: return jsonify({"status": "error", "message": "Falta correo"}), 400
    
    # Lógica de psicología diaria
    mensajes = [
        "Hoy el cielo te pide pausa. No tienes que resolverlo todo en las próximas 24 horas.",
        "Tu energía está en expansión. Es un gran momento para esa conversación pendiente.",
        "La Luna sugiere introspección. Tu refugio hoy es tu propio silencio.",
        "Hay una alineación que favorece tu creatividad. Permítete jugar un poco más.",
        "Momento de poner límites sanos. Decir 'no' a otros es decirte 'sí' a ti misma.",
        "La claridad llega tras la calma. El mapa indica que el caos es temporal.",
        "Hoy tu intuición está afilada. Confía en tu primer pensamiento al despertar."
    ]
    mensaje_hoy = mensajes[datetime.datetime.now().weekday()]

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
                    "mensaje_del_dia": mensaje_hoy
                }
            }), 200
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# (Mantén tus funciones de login() y registro() iguales abajo)
