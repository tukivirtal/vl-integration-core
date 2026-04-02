import os
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# ==========================================
# CONEXIÓN A SUPABASE
# ==========================================
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if url and key:
    supabase: Client = create_client(url, key)
else:
    supabase = None
    print("ADVERTENCIA: Faltan llaves de Supabase en Vercel.", flush=True)

# ==========================================
# RUTA DE REGISTRO
# ==========================================
@app.route('/registro', methods=['POST'])
def registro():
    if not supabase:
        return jsonify({"status": "error", "message": "Base de datos no configurada."}), 500

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

        # 2. El lugar completo viene del buscador inteligente en mayúsculas (Ej: "CARMELO, COLONIA, URUGUAY")
        lugar_completo = data.get('ciudad', '').strip().upper()

        # 3. Empaquetar las coordenadas en la columna JSONB que SÍ tienes (datos_natales)
        datos_natales_json = {
            "geo": {
                "lat": float(data.get('lat')) if data.get('lat') else None,
                "lon": float(data.get('lon')) if data.get('lon') else None
            },
            "auth": "PENDING_CALCULATION"
        }

        # 4. Estructura EXACTA coincidiendo con tu tabla de Supabase (usuarios_refugio)
        nuevo_usuario = {
            "nombre": data.get('nombre'),
            "email": email,
            "fecha_nacimiento": data.get('fecha'),
            "hora_nacimiento": data.get('hora'),
            "ciudad": lugar_completo,
            "pais": data.get('pais', ''), # Quedará vacío porque la ciudad ya trae todo, pero evita errores
            "nivel_suscripcion": "free",
            "datos_natales": datos_natales_json # Aquí entran las coordenadas
        }

        # Insertar en Supabase
        supabase.table('usuarios_refugio').insert(nuevo_usuario).execute()

        return jsonify({
            "status": "exito",
            "message": "¡Tu refugio ha sido generado con éxito!"
        }), 201

    except Exception as e:
        print(f"Error en registro: {str(e)}", flush=True) 
        return jsonify({"status": "error", "message": "Fallo en el núcleo de registro."}), 500
