import base64
import io
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import requests
from PIL import Image, ImageOps, ImageTk

API_URL = "http://localhost:5000"
CAMARA_INDICE = 0            # si no abre tu webcam, prueba con 1
ANCHO_VISTA, ALTO_VISTA = 480, 360


class App:
    def __init__(self, root):
        self.root = root
        root.title("¿Perro o gato? - Cliente app (Python)")
        root.resizable(False, False)

        self.camara = None
        self.ultimo_frame = None   # PIL.Image del último frame de la cámara
        self.imagen = None         # dict: pil, bytes, nombre, origen
        self.foto_tk = None        # referencia para que Tkinter no borre la imagen
        self.cola = queue.Queue()  # comunicación entre el hilo de red y la interfaz

        self._construir_interfaz()
        root.protocol("WM_DELETE_WINDOW", self.cerrar)

    # ---------- Interfaz ----------
    def _construir_interfaz(self):
        marco = ttk.Frame(self.root, padding=16)
        marco.grid()

        ttk.Label(marco, text="¿Perro o gato?", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            marco,
            text="Cliente app · imagen en base64 hacia el servicio Flask",
            foreground="#52606d",
        ).grid(row=1, column=0, sticky="w", pady=(0, 10))

        # Botones principales
        barra = ttk.Frame(marco)
        barra.grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.btn_camara = ttk.Button(barra, text="Usar cámara", command=self.iniciar_camara)
        self.btn_camara.pack(side="left", padx=(0, 8))
        self.btn_archivo = ttk.Button(barra, text="Elegir archivo", command=self.elegir_archivo)
        self.btn_archivo.pack(side="left")

        # Botones de la cámara (solo visibles mientras está activa)
        self.barra_camara = ttk.Frame(marco)
        self.barra_camara.grid(row=3, column=0, sticky="w", pady=(0, 6))
        ttk.Button(self.barra_camara, text="Capturar foto", command=self.capturar_foto).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(self.barra_camara, text="Cancelar", command=self.detener_camara).pack(side="left")
        self.barra_camara.grid_remove()

        # Vista de la imagen
        self.lbl_imagen = tk.Label(marco, bd=0)
        self.lbl_imagen.grid(row=4, column=0, pady=(0, 8))
        self.mostrar_pil(Image.new("RGB", (ANCHO_VISTA, ALTO_VISTA), "#222222"))

        # Botón clasificar
        self.btn_clasificar = ttk.Button(marco, text="Clasificar", command=self.clasificar)
        self.btn_clasificar.grid(row=5, column=0, sticky="w")
        self.btn_clasificar.state(["disabled"])

        # Mensajes de estado / error
        self.estado = tk.StringVar()
        self.lbl_estado = tk.Label(
            marco, textvariable=self.estado, fg="#9b1c1c", wraplength=ANCHO_VISTA, justify="left"
        )
        self.lbl_estado.grid(row=6, column=0, sticky="w", pady=(6, 0))

        # Resultado
        self.marco_resultado = ttk.Frame(marco)
        self.marco_resultado.grid(row=7, column=0, sticky="w", pady=(8, 0))

    def mostrar_pil(self, img):
        """Muestra una imagen PIL centrada en un lienzo de tamaño fijo."""
        vista = img.convert("RGB")
        vista.thumbnail((ANCHO_VISTA, ALTO_VISTA))
        lienzo = Image.new("RGB", (ANCHO_VISTA, ALTO_VISTA), "#222222")
        lienzo.paste(
            vista, ((ANCHO_VISTA - vista.width) // 2, (ALTO_VISTA - vista.height) // 2)
        )
        self.foto_tk = ImageTk.PhotoImage(lienzo)
        self.lbl_imagen.configure(image=self.foto_tk)

    def limpiar_resultado(self):
        for w in self.marco_resultado.winfo_children():
            w.destroy()
        self.estado.set("")

    # ---------- Cámara ----------
    def iniciar_camara(self):
        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
        camara = cv2.VideoCapture(CAMARA_INDICE, backend)
        if not camara.isOpened():
            camara.release()
            messagebox.showerror(
                "Cámara",
                "No se pudo abrir la cámara. Verifica que no la esté usando otra aplicación.",
            )
            return
        self.camara = camara
        self.btn_camara.state(["disabled"])
        self.barra_camara.grid()
        self.limpiar_resultado()
        self.actualizar_camara()

    def actualizar_camara(self):
        if self.camara is None:
            return
        ok, frame = self.camara.read()
        if ok:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.ultimo_frame = Image.fromarray(rgb)
            self.mostrar_pil(self.ultimo_frame)
        self.root.after(30, self.actualizar_camara)

    def detener_camara(self):
        if self.camara is not None:
            self.camara.release()
            self.camara = None
        self.barra_camara.grid_remove()
        self.btn_camara.state(["!disabled"])

    def capturar_foto(self):
        if self.ultimo_frame is None:
            return
        img = self.ultimo_frame
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=90)
        self.imagen = {
            "pil": img,
            "bytes": buffer.getvalue(),
            "nombre": "captura_webcam.jpg",
            "origen": "camara",
        }
        self.detener_camara()
        self.mostrar_pil(img)
        self.limpiar_resultado()
        self.btn_clasificar.state(["!disabled"])

    # ---------- Archivo ----------
    def elegir_archivo(self):
        self.detener_camara()
        ruta = filedialog.askopenfilename(
            title="Elige una imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Todos", "*.*")],
        )
        if not ruta:
            return
        try:
            with open(ruta, "rb") as f:
                datos = f.read()
            img = ImageOps.exif_transpose(Image.open(io.BytesIO(datos))).convert("RGB")
        except Exception as e:
            messagebox.showerror("Archivo", f"No se pudo abrir la imagen:\n{e}")
            return

        self.imagen = {
            "pil": img,
            "bytes": datos,
            "nombre": ruta.replace("\\", "/").split("/")[-1],
            "origen": "archivo",
        }
        self.mostrar_pil(img)
        self.limpiar_resultado()
        self.btn_clasificar.state(["!disabled"])

    # ---------- Clasificar ----------
    def clasificar(self):
        if not self.imagen:
            return
        self.btn_clasificar.state(["disabled"])
        self.limpiar_resultado()
        self.estado.set("Clasificando...")
        self.lbl_estado.configure(fg="#52606d")

        ancho, alto = self.imagen["pil"].size
        payload = {
            "imagen": base64.b64encode(self.imagen["bytes"]).decode("utf-8"),
            "metadata": {
                "cliente": "app-python",
                "nombre_archivo": self.imagen["nombre"],
                "origen": self.imagen["origen"],
                "ancho": ancho,
                "alto": alto,
            },
        }
        # La petición va en otro hilo para que la ventana no se congele
        threading.Thread(target=self._enviar, args=(payload,), daemon=True).start()
        self.root.after(100, self.revisar_cola)

    def _enviar(self, payload):
        try:
            r = requests.post(f"{API_URL}/predict", json=payload, timeout=30)
            data = r.json()
            if not r.ok or not data.get("ok"):
                raise RuntimeError(data.get("error", "Error del servidor"))
            self.cola.put(("ok", data))
        except requests.exceptions.ConnectionError:
            self.cola.put((
                "error",
                "No se pudo conectar con el servidor. ¿Está corriendo Flask (python app.py)?",
            ))
        except Exception as e:
            self.cola.put(("error", str(e)))

    def revisar_cola(self):
        try:
            tipo, contenido = self.cola.get_nowait()
        except queue.Empty:
            self.root.after(100, self.revisar_cola)
            return

        self.btn_clasificar.state(["!disabled"])
        if tipo == "ok":
            self.estado.set("")
            self.mostrar_resultado(contenido)
        else:
            self.lbl_estado.configure(fg="#9b1c1c")
            self.estado.set(contenido)

    def mostrar_resultado(self, data):
        self.limpiar_resultado()
        pred = data["prediccion"]

        ttk.Label(
            self.marco_resultado,
            text=f'{pred["clase"].capitalize()} ({pred["confianza"] * 100:.1f}%)',
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        for clase, p in pred["probabilidades"].items():
            ttk.Label(self.marco_resultado, text=f"{clase}: {p * 100:.1f}%").pack(
                anchor="w", pady=(6, 0)
            )
            ttk.Progressbar(
                self.marco_resultado, length=ANCHO_VISTA, maximum=100, value=p * 100
            ).pack(anchor="w")

        meta = data["metadata"]
        ttk.Label(
            self.marco_resultado,
            text=f'Servidor: {data["tiempo_ms"]} ms · Cliente: {meta.get("cliente")} · Origen: {meta.get("origen")}',
            foreground="#52606d",
        ).pack(anchor="w", pady=(8, 0))

    # ---------- Cierre ----------
    def cerrar(self):
        self.detener_camara()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()