import os
from werkzeug.security import generate_password_hash
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# Función para obtener el cliente de Supabase bajo demanda
def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("CRÍTICO: SUPABASE_URL o SUPABASE_KEY no encontradas en Vercel.", flush=True)
        return None
    
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"Error al inicializar cliente Supabase: {str(e)}", flush=True)
        return None

# ==========================================
# RUTA DE REGISTRO
# ==========================================
@app.route('/registro', methods=['POST'])
def registro():
    supabase = get_supabase_client()
    
    if not supabase:
        return jsonify({"status": "error", "message": "Error interno: Base de datos no configurada."}), 500

    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Correo y contraseña son obligatorios."}), 400

    try:
        # 1. Verificar si el correo ya existe
        respuesta_busqueda = supabase.table('usuarios_refugio').select('email').eq('email', email).execute()

        if len(respuesta_busqueda.data) > 0:
            return jsonify({
                "status": "existe",
                "message": "Este correo ya tiene un refugio creado. Por favor, accede a tu cuenta en el menú superior."
            }), 200

        # 2. Encriptar la contraseña (¡Magia de Seguridad!)
        if len(password) < 6:
            return jsonify({"status": "error", "message": "La contraseña debe tener al menos 6 caracteres."}), 400
        
        contrasena_encriptada = generate_password_hash(password)

        # 3. El lugar completo en mayúsculas
        lugar_completo = data.get('ciudad', '').strip().upper()

        # 4. Empaquetar las coordenadas JSONB
        datos_natales_json = {
            "geo": {
                "lat": float(data.get('lat')) if data.get('lat') else None,
                "lon": float(data.get('lon')) if data.get('lon') else None
            },
            "auth": "PENDING_CALCULATION"
        }
# ==========================================
# RUTA PARA OBTENER DATOS DEL REFUGIO
# ==========================================
@app.route('/obtener_datos', methods=['POST'])
def obtener_datos():
    supabase = get_supabase_client()
    if not supabase:
        return jsonify({"status": "error", "message": "Base de datos desconectada."}), 500

    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"status": "error", "message": "Email no proporcionado."}), 400

    try:
        # Buscar al usuario por su email
        respuesta = supabase.table('usuarios_refugio').select('*').eq('email', email).execute()

        if len(respuesta.data) > 0:
            usuario = respuesta.data[0]
            
            # Aquí en el futuro puedes procesar las coordenadas de la NASA.
            # Por ahora, devolvemos los datos guardados para inyectarlos en la web.
            return jsonify({
                "status": "exito",
                "datos": {
                    "nombre": usuario.get('nombre', 'Exploradora'),
                    "ciudad": usuario.get('ciudad', 'Tu ciudad'),
                    "fecha": usuario.get('fecha_nacimiento', '')
                }
            }), 200
        else:
            return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404

    except Exception as e:
        print(f"Error al obtener datos: {str(e)}", flush=True)
        return jsonify({"status": "error", "message": "Error interno."}), 500
        
        # 5. Estructura FINAL insertando la contraseña encriptada
        nuevo_usuario = {
            "nombre": data.get('nombre'),
            "email": email,
            "contrasena": contrasena_encriptada, # <- SE GUARDA ENCRIPTADA
            "fecha_nacimiento": data.get('fecha'),
            "hora_nacimiento": data.get('hora'),
            "ciudad": lugar_completo,
            "pais": data.get('pais', ''),
            "nivel_suscripcion": "free",
            "datos_natales": datos_natales_json 
        }

        # Insertar en Supabase
        supabase.table('usuarios_refugio').insert(nuevo_usuario).execute()

        return jsonify({
            "status": "exito",
            "message": "¡Tu refugio ha sido generado con éxito!"
        }), 201

    except Exception as e:
        print(f"Error en registro con BD: {str(e)}", flush=True) 
        return jsonify({"status": "error", "message": "Fallo en el núcleo de registro."}), 500
