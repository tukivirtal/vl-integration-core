import os
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
    # Obtener el cliente DENTRO de la función para evitar problemas de contexto global
    supabase = get_supabase_client()
    
    if not supabase:
        return jsonify({"status": "error", "message": "Error interno: Base de datos no configurada o inaccesible."}), 500

    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"status": "error", "message": "El correo es obligatorio."}), 400

    try:
        # 1. Verificar si el correo ya existe
        respuesta_busqueda = supabase.table('usuarios_refugio').select('email').eq('email', email).execute()

        if len(respuesta_busqueda.data) > 0:
            return jsonify({
                "status": "existe",
                "message": "Este correo ya tiene un refugio creado. Por favor, accede a tu cuenta en el menú superior."
            }), 200

        # 2. El lugar completo viene del buscador inteligente en mayúsculas
        lugar_completo = data.get('ciudad', '').strip().upper()

        # 3. Empaquetar las coordenadas en la columna JSONB que SÍ tienes (datos_natales)
        datos_natales_json = {
            "geo": {
                "lat": float(data.get('lat')) if data.get('lat') else None,
                "lon": float(data.get('lon')) if data.get('lon') else None
            },
            "auth": "PENDING_CALCULATION"
        }

        # 4. Estructura EXACTA coincidiendo con tu tabla de Supabase
        nuevo_usuario = {
            "nombre": data.get('nombre'),
            "email": email,
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
