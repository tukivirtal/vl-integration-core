from flask import Flask, request
import requests

app = Flask(__name__)

# TU WEBHOOK DE MAKE
MAKE_WEBHOOK = "https://hook.us2.make.com/o74gpcv5xlre3cvwnh5yr0kg6w15vrxv"


@app.route('/registro', methods=['POST'])
def registro():
    if not supabase:
        return jsonify({"status": "error", "message": "Error interno: Base de datos no configurada."}), 500

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

        # 2. Formatear lugar (Ej: "Carmelo, Uruguay")
        lugar_original = f"{data.get('ciudad', '')}, {data.get('pais', '')}".strip(", ")

        # 3. Empaquetar en formato JSON para datos_natales
        datos_natales_json = {
            "fecha": data.get('fecha'),
            "hora_nacimiento": data.get('hora'),
            "lugar_original": lugar_original.upper() # Lo pasamos a mayúsculas como en tu ejemplo
        }

        # 4. Empaquetar en formato JSON para mapatotal (Coordenadas)
        mapatotal_json = {
            "geo": {
                "lat": float(data.get('lat')) if data.get('lat') else None,
                "lon": float(data.get('lon')) if data.get('lon') else None
            },
            "auth": "PENDING_CALCULATION" # Estado inicial hasta que se calcule su carta
        }

        # 5. Estructura final a insertar en Supabase
        nuevo_usuario = {
            "nombre": data.get('nombre'),
            "email": email,
            "nivel_suscripcion": "free",
            "datos_natales": datos_natales_json, # Entra directo al campo JSONB
            "mapatotal": mapatotal_json          # Entra directo al campo JSONB
        }

        # Insertar en Supabase
        supabase.table('usuarios_refugio').insert(nuevo_usuario).execute()

        return jsonify({
            "status": "exito",
            "message": "¡Tu refugio ha sido generado con éxito!"
        }), 201

    except Exception as e:
        print(f"Error en registro: {str(e)}", flush=True) # Para ver el error exacto en los logs de Vercel
        return jsonify({"status": "error", "message": "Fallo en el núcleo de registro."}), 500
