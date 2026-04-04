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
    
    res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
    if len(res.data) > 0:
        u = res.data[0]
        nombre = u.get('nombre', 'Exploradora')
        
        # --- MOTOR DINÁMICO DE PILARES ---
        # Asignamos un arquetipo diferente basado en la longitud de su nombre (simulando variabilidad)
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
        
        # Seleccionamos dinámicamente
        idx_base = len(nombre) % 3
        idx_filtro = (len(nombre) + 1) % 3
        
        pilar_1 = arquetipos_base[idx_base]
        pilar_2 = arquetipos_filtro[idx_filtro]
        # ---------------------------------

        return jsonify({
            "status": "exito", 
            "datos": {
                "nombre": nombre, 
                "ciudad": u.get('ciudad', 'Tu ciudad'), 
                "fecha": u.get('fecha_nacimiento', '--/--/----'),
                "mensaje_del_dia": "La claridad llega tras la calma.", # (Mantén tu lógica de mensajes aquí)
                "pilar1": pilar_1,
                "pilar2": pilar_2
            }
        }), 200
        
    return jsonify({"status": "error", "message": "No se hallaron datos."}), 404
