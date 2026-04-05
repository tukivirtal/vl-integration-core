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
# ENRUTADOR MAESTRO
# ==========================================
@app.route('/', defaults={'path': ''}, methods=['POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['POST', 'OPTIONS'])
def enrutador(path):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    
    try:
        ruta_solicitada = request.path
        
        if 'login' in ruta_solicitada: return login()
        if 'registro' in ruta_solicitada: return registro()
        if 'obtener_datos' in ruta_solicitada: return obtener_datos()
            
        return jsonify({"status": "error", "message": "Ruta no encontrada"}), 404
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Error interno: " + str(e)}), 500

# ==========================================
# LÓGICA DE REGISTRO
# ==========================================
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
        
        # Filtro de seguridad para coordenadas
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

# ==========================================
# LÓGICA DE LOGIN
# ==========================================
def login():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Credenciales incompletas."}), 400
    
    try:
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
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# LÓGICA DE OBTENER DATOS (Pilares dinámicos)
# ==========================================
def obtener_datos():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error", "message": "Falta BD."}), 500
    
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    
    try:
        res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
        if len(res.data) > 0:
            u = res.data[0]
            nombre = u.get('nombre', 'Exploradora')
            
            # Textos dinámicos
            arquetipos_base = [
                {"elemento": "Elemento Fuego", "titulo": "Tu Impulso", "texto": "Estás diseñada para iniciar y transformar. Tu mente busca la acción instintivamente. Tu principal fuga de energía es el agotamiento por no saber detenerte o por cargar con los miedos de otros."},
                {"elemento": "Elemento Tierra", "titulo": "Tu Gravedad", "texto": "Estás diseñada para materializar y sostener. Tu mente busca la estructura. Tu principal fuga de energía radica en asumir el peso de las dinámicas de otros, confundiendo tu capacidad con un falso deber."},
                {"elemento": "Elemento Agua", "titulo": "Tu Resonancia", "texto": "Estás diseñada para sentir y nutrir. Tu mente procesa el mundo a través de la empatía profunda. Tu fuga de energía es absorber emociones ajenas como si fueran tuyas, perdiendo tu centro."}
            ]
            arquetipos_filtro = [
                {"elemento": "Elemento Aire", "texto": "Por dentro tu mente sobre-analiza cada escenario buscando entenderlo todo. Te drenas cuando no hay claridad mental o comunicación."},
                {"elemento": "Elemento Fuego", "texto": "Por dentro procesas el caos a través de la impaciencia. Necesitas que las cosas avancen y te frustras profundamente ante el estancamiento ajeno."},
                {"elemento": "Elemento Tierra", "texto": "Por dentro buscas garantías. Necesitas saber que el suelo es firme antes de dar un paso, lo que a veces te encierra en la parálisis por análisis."}
            ]
            
            idx_base = len(nombre) % 3
            idx_filtro = (len(nombre) + 1) % 3
            
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

            return jsonify({
                "status": "exito", 
                "datos": {
                    "nombre": nombre, 
                    "ciudad": u.get('ciudad', 'Tu ciudad'), 
                    "fecha": u.get('fecha_nacimiento', '--/--/----'),
                    "mensaje_del_dia": mensaje_hoy,
                    "pilar1": arquetipos_base[idx_base],
                    "pilar2": arquetipos_filtro[idx_filtro]
                }
            }), 200
            
        return jsonify({"status": "error", "message": "No se hallaron datos."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
