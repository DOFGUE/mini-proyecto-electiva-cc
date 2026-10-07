import base64
import io
import os
import time

import keras
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image, ImageOps

app = Flask(__name__)
CORS(app)  # permite llamadas desde el cliente web (React)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

# ---------- Cargar el modelo al iniciar ----------
RUTA_MODELO = os.path.join(os.path.dirname(__file__), "modelos", "perros_gatos.keras")
MODELO = keras.models.load_model(RUTA_MODELO)
print("Modelo de perros y gatos cargado.")


# ---------- Utilidades ----------
def decodificar_imagen(b64: str) -> Image.Image:
    # Acepta "data:image/jpeg;base64,xxxx" o solo "xxxx"
    if b64.strip().startswith("data:") and "," in b64:
        b64 = b64.split(",", 1)[1]
    datos = base64.b64decode(b64)
    img = Image.open(io.BytesIO(datos))
    img = ImageOps.exif_transpose(img)  # corrige fotos rotadas del celular
    return img


def predecir(img: Image.Image) -> dict:
    img = img.convert("RGB").resize((180, 180))
    arr = np.expand_dims(np.array(img, dtype="float32"), 0)  # (1, 180, 180, 3)
    logit = float(MODELO.predict(arr, verbose=0)[0][0])
    p_perro = float(1 / (1 + np.exp(-logit)))  # sigmoide
    p_gato = 1 - p_perro
    return {
        "clase": "perro" if p_perro >= 0.5 else "gato",
        "confianza": max(p_perro, p_gato),
        "probabilidades": {"gato": p_gato, "perro": p_perro},
    }


# ---------- Endpoints ----------
@app.get("/health")
def health():
    return jsonify({"ok": True, "modelo": "perros_gatos"})


@app.post("/predict")
def predict():
    inicio = time.time()
    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"ok": False, "error": "Se esperaba un JSON"}), 400

    imagen_b64 = datos.get("imagen")
    metadata = datos.get("metadata", {})

    if not imagen_b64:
        return jsonify({"ok": False, "error": "Falta el campo 'imagen'"}), 400

    try:
        img = decodificar_imagen(imagen_b64)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Imagen inválida: {e}"}), 400

    return jsonify({
        "ok": True,
        "prediccion": predecir(img),
        "metadata": metadata,
        "tiempo_ms": round((time.time() - inicio) * 1000, 1),
    })


if __name__ == "__main__":
    # 0.0.0.0 permite que el celular (misma red WiFi) se conecte
    app.run(host="0.0.0.0", port=5000, debug=False)