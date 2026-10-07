import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:5000";

export default function App() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const [camaraActiva, setCamaraActiva] = useState(false);
  const [imagen, setImagen] = useState(null); // { dataUrl, nombre, origen }
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  // Conectar el stream al <video> cuando la cámara se activa
  useEffect(() => {
    if (camaraActiva && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [camaraActiva]);

  // Apagar la cámara al salir de la página
  useEffect(() => {
    return () => detenerCamara();
  }, []);

  function detenerCamara() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setCamaraActiva(false);
  }

  async function iniciarCamara() {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      streamRef.current = stream;
      setCamaraActiva(true);
    } catch {
      setError("No se pudo acceder a la cámara. Revisa los permisos del navegador.");
    }
  }

  function capturarFoto() {
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.9);

    setImagen({ dataUrl, nombre: `captura_${Date.now()}.jpg`, origen: "camara" });
    setResultado(null);
    detenerCamara();
  }

  function onArchivo(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    detenerCamara();
    const reader = new FileReader();
    reader.onload = () => {
      setImagen({ dataUrl: reader.result, nombre: file.name, origen: "archivo" });
      setResultado(null);
      setError("");
    };
    reader.readAsDataURL(file);
  }

  async function clasificar() {
    if (!imagen) return;
    setCargando(true);
    setError("");
    setResultado(null);

    try {
      // Quitamos el prefijo "data:image/jpeg;base64," y enviamos solo el base64
      const base64 = imagen.dataUrl.split(",")[1];

      const resp = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          imagen: base64,
          metadata: {
            cliente: "web",
            nombre_archivo: imagen.nombre,
            origen: imagen.origen,
          },
        }),
      });

      const data = await resp.json();
      if (!resp.ok || !data.ok) {
        throw new Error(data.error || "Error del servidor");
      }
      setResultado(data);
    } catch (e) {
      setError(`No se pudo clasificar: ${e.message}`);
    } finally {
      setCargando(false);
    }
  }

  const pct = (x) => (x * 100).toFixed(1);

  return (
    <div className="app">
      <h1>¿Perro o gato?</h1>
      <p className="subtitulo">Cliente web · envía la imagen en base64 al servicio Flask</p>

      <div className="acciones">
        <button className="btn" onClick={iniciarCamara} disabled={camaraActiva}>
          Usar cámara
        </button>
        <label className="btn secundario">
          Elegir archivo
          <input type="file" accept="image/*" onChange={onArchivo} hidden />
        </label>
      </div>

      {camaraActiva && (
        <>
          <video ref={videoRef} className="vista" autoPlay playsInline muted />
          <div className="acciones">
            <button className="btn verde" onClick={capturarFoto}>
              Capturar foto
            </button>
            <button className="btn secundario" onClick={detenerCamara}>
              Cancelar
            </button>
          </div>
        </>
      )}

      {imagen && !camaraActiva && (
        <>
          <img src={imagen.dataUrl} alt="Vista previa" className="vista" />
          <div className="acciones">
            <button className="btn verde" onClick={clasificar} disabled={cargando}>
              {cargando ? "Clasificando..." : "Clasificar"}
            </button>
          </div>
        </>
      )}

      {error && <div className="error">{error}</div>}

      {resultado && (
        <div className="resultado">
          <h2>
            {resultado.prediccion.clase} ({pct(resultado.prediccion.confianza)}%)
          </h2>

          {Object.entries(resultado.prediccion.probabilidades).map(([clase, p]) => (
            <div key={clase}>
              <div>
                {clase}: {pct(p)}%
              </div>
              <div className="barra">
                <div style={{ width: `${pct(p)}%` }} />
              </div>
            </div>
          ))}

          <div className="meta">
            Tiempo del servidor: {resultado.tiempo_ms} ms · Cliente: {resultado.metadata.cliente} ·
            Origen: {resultado.metadata.origen}
          </div>
        </div>
      )}
    </div>
  );
}