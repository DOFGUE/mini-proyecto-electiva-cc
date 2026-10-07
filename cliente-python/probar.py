import base64
import sys

import requests

URL = "http://localhost:5000/predict"

def predecir(ruta_imagen: str):
    with open(ruta_imagen, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "imagen": b64,
        "metadata": {"cliente": "app-python", "nombre_archivo": ruta_imagen},
    }
    r = requests.post(URL, json=payload, timeout=30)
    print(r.status_code)
    print(r.json())

if __name__ == "__main__":
    # uso: python probar.py mi_gato.jpg
    predecir(sys.argv[1])