# Clasificador de perros y gatos

Proyecto de clasificación de imágenes. Un **servicio web en Python (Flask)** carga un modelo entrenado con Keras y responde a **tres clientes** que le envían una imagen codificada en **base64** junto con *metadata*, todo dentro de un JSON.

| Cliente | Tecnología | Fuentes de imagen |
|---|---|---|
| Web | React (Vite) | Cámara + archivo |
| Móvil | React Native (Expo) | Cámara + galería |
| App | Python (Tkinter + OpenCV) | Webcam + archivo |

**Autores:** _(completa aquí)_

---

## 1. Arquitectura

```
Cliente web ─────┐
Cliente móvil ───┼──  POST /predict  { imagen (base64), metadata }  ──►  Servicio Flask
Cliente app ─────┘                                                        │ decodifica el base64
                                                                          │ preprocesa la imagen (180x180)
      ◄────  { clase, confianza, probabilidades, ... }  ─────────────────┘ modelo .keras -> predicción
```

## 2. Estructura de carpetas

```
proyecto-IA/
├── requirements.txt
├── .gitignore
├── entrenamiento/
│   └── train_perros_gatos.py     # entrena el modelo y lo guarda como .keras
├── servidor/
│   ├── app.py                    # servicio web Flask
│   └── modelos/
│       └── perros_gatos.keras    # modelo entrenado
├── cliente-python/
│   ├── app_cliente.py            # app de escritorio (Tkinter)
│   └── probar.py                 # cliente por consola (prueba rápida)
├── cliente-web/                  # React + Vite
└── cliente-movil/                # React Native + Expo
```

## 3. Requisitos

- **Python 3.10, 3.11 o 3.12** (TensorFlow aún no funciona con versiones más nuevas).
- **Node.js (LTS)**, que incluye `npm`.
- **VS Code** (recomendado).
- **Expo Go** instalado en el celular Android (Play Store).
- Cuenta de Google para entrenar en **Google Colab** (opcional, pero recomendado).

---

## 4. Preparar el entorno de Python

Desde la raíz del proyecto:

```bash
python -m venv venv          # en Windows también sirve: py -3.12 -m venv venv
```

Activar el entorno:

```bash
# Git Bash (Windows)
source venv/Scripts/activate

# PowerShell / CMD (Windows)
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

Instalar las dependencias (la terminal debe mostrar `(venv)`):

```bash
pip install -r requirements.txt
```

Si no tienes el archivo `requirements.txt`:

```bash
pip install tensorflow flask flask-cors pillow numpy matplotlib requests opencv-python
```

> **Importante:** si el proyecto está dentro de OneDrive, el entorno virtual puede fallar al crearse. Guárdalo en una carpeta fuera de OneDrive (por ejemplo `C:\proyectos\`).

---

## 5. Entrenar el modelo (solo una vez)

El script `entrenamiento/train_perros_gatos.py` descarga el dataset *Cats vs Dogs* (≈786 MB), limpia las imágenes corruptas, entrena la red y guarda `perros_gatos.keras`.

### Opción A: Google Colab (recomendada)

1. Entra a [colab.research.google.com](https://colab.research.google.com) y crea un cuaderno nuevo.
2. **Entorno de ejecución → Cambiar tipo de entorno de ejecución →** elige **GPU T4**.
3. Sube `train_perros_gatos.py` desde el panel de archivos (icono de carpeta).
4. En una celda ejecuta:
   ```python
   !python -u train_perros_gatos.py
   ```
5. Al terminar, descarga el modelo:
   ```python
   from google.colab import files
   files.download("perros_gatos.keras")
   ```
6. Copia el archivo descargado a `servidor/modelos/`.

### Opción B: en tu computador

```bash
cd entrenamiento
python train_perros_gatos.py
```

Sin GPU tarda mucho; para una prueba rápida baja `EPOCHS` a 3 dentro del script. El modelo se guarda directamente en `servidor/modelos/`.

---

## 6. Ejecutar el servidor (siempre primero)

```bash
cd servidor
python app.py
```

Debe aparecer `Modelo de perros y gatos cargado.` Verifica en el navegador:

```
http://localhost:5000/health
```

Respuesta esperada: `{"modelo":"perros_gatos","ok":true}`.

**Deja esta terminal abierta** mientras pruebas los clientes.

---

## 7. Cliente app (Python)

Abre otra terminal con `(venv)` activo.

**Interfaz gráfica** (archivo o webcam):

```bash
cd cliente-python
python app_cliente.py
```

**Prueba rápida por consola:**

```bash
cd cliente-python
python probar.py gato.jpg
```

Notas:
- Si la webcam no abre, cierra otras aplicaciones que la usen (Zoom, Teams, navegador) o cambia `CAMARA_INDICE = 0` por `1` en `app_cliente.py`.
- Si aparece `No module named tkinter`, reinstala Python marcando **tcl/tk and IDLE** en las opciones del instalador.

---

## 8. Cliente web (React)

En otra terminal (no necesita el entorno de Python):

```bash
cd cliente-web
npm install        # solo la primera vez
npm run dev
```

Abre la dirección que muestra la terminal (normalmente `http://localhost:5173`).

- **Usar cámara:** el navegador pide permiso; pulsa *Capturar foto* y luego *Clasificar*.
- **Elegir archivo:** selecciona una imagen y pulsa *Clasificar*.

La URL del servidor está en la constante `API_URL` de `src/App.jsx`.

---

## 9. Cliente móvil (React Native + Expo)

1. Instala **Expo Go** en tu celular Android.
2. Conecta el celular y el computador a la **misma red WiFi**.
3. Averigua la IP de tu computador:
   ```bash
   ipconfig
   ```
   Copia la **Dirección IPv4** del adaptador WiFi (por ejemplo `192.168.1.15`).
4. Abre `cliente-movil/App.js` y cambia la primera constante:
   ```js
   const API_URL = "http://192.168.1.15:5000";
   ```
5. **Prueba de conexión:** con el servidor corriendo, abre en el navegador **del celular** `http://TU_IP:5000/health`. Debe mostrar `ok: true`.
6. Inicia la app:
   ```bash
   cd cliente-movil
   npm install        # solo la primera vez
   npx expo start
   ```
7. En Expo Go, pulsa **Scan QR code** y escanea el código que aparece en la terminal.

Si el celular no logra conectarse:
- Permite **Python** en el Firewall de Windows (redes privadas).
- Marca la red WiFi como **Privada** en Windows.
- En redes de universidad u oficina suele estar bloqueada la comunicación entre dispositivos: usa la **zona WiFi del celular** y conecta el computador a ella (la IP cambia, vuelve a ejecutar `ipconfig`).
- Si la app no carga, prueba `npx expo start --tunnel`. Esto solo ayuda a cargar la app; el servidor Flask se sigue consultando por la IP local.

---

## 10. API del servicio

### `GET /health`

Comprueba que el servidor y el modelo están activos.

```json
{ "ok": true, "modelo": "perros_gatos" }
```

### `POST /predict`

**Petición** (`Content-Type: application/json`):

```json
{
  "imagen": "<imagen en base64, sin el prefijo data:...>",
  "metadata": {
    "cliente": "movil",
    "nombre_archivo": "foto.jpg",
    "origen": "camara"
  }
}
```

**Respuesta correcta (200):**

```json
{
  "ok": true,
  "prediccion": {
    "clase": "gato",
    "confianza": 0.94,
    "probabilidades": { "gato": 0.94, "perro": 0.06 }
  },
  "metadata": { "cliente": "movil", "nombre_archivo": "foto.jpg", "origen": "camara" },
  "tiempo_ms": 85.2
}
```

**Errores (400):**

```json
{ "ok": false, "error": "Falta el campo 'imagen'" }
{ "ok": false, "error": "Imagen inválida: ..." }
```

El campo `metadata` es libre: el servidor lo devuelve tal cual.

---

## 11. Problemas frecuentes

| Problema | Causa probable | Solución |
|---|---|---|
| `Failed to fetch` / `Network request failed` | El servidor no está corriendo o la URL es incorrecta | Inicia `python app.py` y revisa `API_URL` |
| El celular no conecta | IP incorrecta, firewall o red que aísla dispositivos | Prueba `http://TU_IP:5000/health` en el celular; usa la zona WiFi del celular |
| `pip install tensorflow` falla | Versión de Python no compatible (3.13 o 3.14) | Usa Python 3.12 |
| Error al crear el `venv` | Proyecto dentro de OneDrive | Mueve el proyecto fuera de OneDrive |
| `FileNotFoundError ... perros_gatos.keras` | Falta el modelo entrenado | Cópialo a `servidor/modelos/` |
| `Imagen inválida` | El base64 viene con prefijo `data:` mal cortado o no son los bytes de una imagen | Revisa cómo se codifica la imagen en el cliente |
| La webcam no abre | Otra aplicación la está usando | Ciérrala o cambia `CAMARA_INDICE` |

---

## 12. Notas

- Las carpetas `venv/`, `node_modules/` y `PetImages/` no se suben al repositorio (ver `.gitignore`). Después de clonar hay que ejecutar `pip install -r requirements.txt` y `npm install` en cada cliente.
- Dentro de `cliente-movil` pueden aparecer `.claude/`, `AGENTS.md` y `CLAUDE.md`. Los genera `create-expo-app` por defecto para asistentes de código con IA; no afectan a la app y se pueden borrar.
- El servidor usa `host="0.0.0.0"` para que el celular pueda conectarse desde la red local. En producción conviene restringirlo y usar HTTPS.
