import os
import datetime
from anthropic import Anthropic
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
# NUEVA LÓGICA MATEMÁTICA ESTRICTA (Para que la IA no adivine)
# ==========================================
def calcular_signo_y_elemento(fecha_str):
    if not fecha_str or fecha_str == 'Desconocida':
        return "Aries", "Fuego"
    try:
        partes = fecha_str.split('-')
        m = int(partes[1])
        d = int(partes[2])
        if (m == 3 and d >= 21) or (m == 4 and d <= 19): return "Aries", "Fuego"
        if (m == 4 and d >= 20) or (m == 5 and d <= 20): return "Tauro", "Tierra"
        if (m == 5 and d >= 21) or (m == 6 and d <= 20): return "Géminis", "Aire"
        if (m == 6 and d >= 21) or (m == 7 and d <= 22): return "Cáncer", "Agua"
        if (m == 7 and d >= 23) or (m == 8 and d <= 22): return "Leo", "Fuego"
        if (m == 8 and d >= 23) or (m == 9 and d <= 22): return "Virgo", "Tierra"
        if (m == 9 and d >= 23) or (m == 10 and d <= 22): return "Libra", "Aire"
        if (m == 10 and d >= 23) or (m == 11 and d <= 21): return "Escorpio", "Agua"
        if (m == 11 and d >= 22) or (m == 12 and d <= 21): return "Sagitario", "Fuego"
        if (m == 12 and d >= 22) or (m == 1 and d <= 19): return "Capricornio", "Tierra"
        if (m == 1 and d >= 20) or (m == 2 and d <= 18): return "Acuario", "Aire"
        return "Piscis", "Agua"
    except:
        return "Aries", "Fuego"

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
        if 'webhook_paypal_Refugio' in ruta_solicitada: return webhook_paypal_Refugio()
        if 'chat' in ruta_solicitada: return chat_oraculo()
            
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
                "datos": {
                    "nombre": usuario.get('nombre'), 
                    "email": usuario.get('email'),
                    "nivel": usuario.get('nivel_suscripcion'),
                    "fecha": usuario.get('fecha_nacimiento')
                }
            }), 200
            
        return jsonify({"status": "error", "message": "Contraseña incorrecta."}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# LÓGICA DE OBTENER DATOS (Para panel Free)
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

            return jsonify({
                "status": "exito", 
                "datos": {
                    "nombre": nombre, 
                    "ciudad": u.get('ciudad', 'Tu ciudad'), 
                    "fecha": u.get('fecha_nacimiento', '--/--/----'),
                    "pilar1": arquetipos_base[idx_base],
                    "pilar2": arquetipos_filtro[idx_filtro]
                }
            }), 200
            
        return jsonify({"status": "error", "message": "No se hallaron datos."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# WEBHOOK DE PAYPAL
# ==========================================
def webhook_paypal_Refugio():
    supabase = get_supabase_client()
    if not supabase: return jsonify({"status": "error"}), 500

    data = request.get_json(silent=True) or {}
    event_type = data.get('event_type')
    
    if event_type == 'PAYMENT.CAPTURE.COMPLETED':
        try:
            resource = data.get('resource', {})
            email_pagador = None
            
            if 'custom_id' in resource:
                email_pagador = resource['custom_id']
            
            if not email_pagador and 'payer' in resource and 'email_address' in resource['payer']:
                email_pagador = resource['payer']['email_address']
                
            if email_pagador:
                supabase.table('usuarios_refugio').update({"nivel_suscripcion": "premium"}).eq('email', email_pagador).execute()
                print(f"Venta Refugio exitosa: {email_pagador} ascendido a PREMIUM.", flush=True)
                
        except Exception as e:
            print(f"Error procesando webhook de Refugio: {str(e)}", flush=True)
            
    return jsonify({"status": "recibido"}), 200

# ==========================================
# CEREBRO IA: EL ORÁCULO DE REFUGIO
# ==========================================
def chat_oraculo():
    supabase = get_supabase_client()
    api_key_anthropic = os.environ.get("ANTHROPIC_API_KEY")
    
    if not supabase or not api_key_anthropic: 
        return jsonify({"status": "error", "message": "Faltan credenciales del sistema central."}), 500
        
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    mensaje_usuaria = data.get('mensaje')
    
    if not email or not mensaje_usuaria:
        return jsonify({"status": "error", "message": "Faltan datos de consulta para el Oráculo."}), 400
        
    try:
        res = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()
        if len(res.data) == 0:
            return jsonify({"status": "error", "message": "Usuario no encontrado en la bóveda."}), 404
            
        usuario = res.data[0]
        nombre = usuario.get('nombre', 'Exploradora')
        fecha_nac = usuario.get('fecha_nacimiento', 'Desconocida')
        ciudad_nac = usuario.get('ciudad', 'Desconocida')
        
        # Aquí calculamos con precisión absoluta usando Python
        signo_exacto, elemento_exacto = calcular_signo_y_elemento(fecha_nac)
        
        system_prompt = f"""
        Eres el "Oráculo de Refugio", una inteligencia analítica basada en cálculos astronómicos (efemérides JPL/NASA), psicología profunda (junguiana) y filosofía práctica estoica.

        [DATOS NATALES DE LA USUARIA ACTUAL]
        Nombre: {nombre}
        Fecha de Nacimiento: {fecha_nac}
        Ciudad de Nacimiento: {ciudad_nac}
        Signo Solar Estricto: {signo_exacto}
        Elemento Dominante: {elemento_exacto}

        [INSTRUCCIÓN VITAL DE PERSONALIZACIÓN]
        Ya NO necesitas deducir su signo zodiacal. Es un hecho innegable que su Signo Solar es {signo_exacto} y su Elemento Dominante es el {elemento_exacto}. Utiliza esta información exacta para anclar tu respuesta a su realidad natal. Jamás sugieras un signo diferente.

        [REGLAS DE COMPORTAMIENTO Y TONO]
        1. Tu tono es profundo, sobrio, analítico y empático, pero NO compasivo. Suenas como un analista sabio y objetivo.
        2. NO uses frases cliché de autoayuda (ej. "todo pasa por algo", "tú puedes", "sé fuerte", "el universo te protege").
        3. NO uses emojis. Cero. Tu comunicación es puramente textual y literaria.
        4. Eres directo. Si hay una fricción psicológica evidente en su mapa, exponla con respeto pero sin anestesia.

        [LIMITACIONES LEGALES - ESTRICTAS]
        1. NUNCA le digas a la usuaria qué decisión específica tomar. Tú solo iluminas el mapa y los patrones de su psique; ella toma la decisión.
        2. No ofrezcas consejos médicos, financieros o legales bajo ninguna circunstancia.

        [ESTRUCTURA OBLIGATORIA DE LA RESPUESTA]
        Tu respuesta debe tener MÁXIMO TRES PÁRRAFOS CORTOS (no más de 3-4 oraciones cada uno):
        - Párrafo 1 (Validación): Valida la emoción o duda que presenta la usuaria explicando de dónde proviene usando su Signo Solar ({signo_exacto}) y/o su elemento dominante ({elemento_exacto}).
        - Párrafo 2 (El Patrón): Explica la sombra o el patrón repetitivo inconsciente que se está activando (visión junguiana) que le causa fricción en este tema.
        - Párrafo 3 (La Acción): Cierra con una instrucción estoica o una pregunta de auto-reflexión poderosa para que ella asuma la responsabilidad de su siguiente paso.
        """
        
        client = Anthropic(api_key=api_key_anthropic)
        
        respuesta_ia = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": mensaje_usuaria}
            ]
        )
        
        texto_final = respuesta_ia.content[0].text
        
        return jsonify({"status": "exito", "respuesta": texto_final}), 200
        
    except Exception as e:
        print(f"Error en Oráculo IA: {str(e)}", flush=True)
        return jsonify({"status": "error", "message": "Interferencia en la bóveda celeste al conectar con el Oráculo. Intenta de nuevo en unos minutos."}), 500
