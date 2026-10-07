import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import * as ImagePicker from "expo-image-picker";

// ⚠️ Cambia por la IP de tu computador
const API_URL = "http://192.168.40.14:5000";

export default function App() {
  const [imagen, setImagen] = useState(null); // { uri, base64, nombre, origen, ancho, alto }
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  function guardarAsset(asset, origen) {
    setImagen({
      uri: asset.uri,
      base64: asset.base64,
      nombre: asset.fileName ?? `${origen}_${Date.now()}.jpg`,
      origen,
      ancho: asset.width,
      alto: asset.height,
    });
    setResultado(null);
    setError("");
  }

  async function tomarFoto() {
    const permiso = await ImagePicker.requestCameraPermissionsAsync();
    if (!permiso.granted) {
      Alert.alert("Permiso requerido", "Necesitamos acceso a la cámara para tomar la foto.");
      return;
    }
    const res = await ImagePicker.launchCameraAsync({
      mediaTypes: ["images"],
      quality: 0.7, // comprime para que el envío sea más rápido
      base64: true,
    });
    if (!res.canceled) guardarAsset(res.assets[0], "camara");
  }

  async function elegirDeGaleria() {
    // En galería no hace falta pedir permiso
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.7,
      base64: true,
    });
    if (!res.canceled) guardarAsset(res.assets[0], "galeria");
  }

  async function clasificar() {
    if (!imagen?.base64) return;
    setCargando(true);
    setError("");
    setResultado(null);

    const controlador = new AbortController();
    const temporizador = setTimeout(() => controlador.abort(), 30000);

    try {
      const resp = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          imagen: imagen.base64,
          metadata: {
            cliente: "movil",
            nombre_archivo: imagen.nombre,
            origen: imagen.origen,
            ancho: imagen.ancho,
            alto: imagen.alto,
          },
        }),
        signal: controlador.signal,
      });

      const data = await resp.json();
      if (!resp.ok || !data.ok) {
        throw new Error(data.error || "Error del servidor");
      }
      setResultado(data);
    } catch (e) {
      if (e.name === "AbortError") {
        setError("El servidor tardó demasiado en responder.");
      } else if (e.message?.includes("Network request failed")) {
        setError(
          "No se pudo conectar con el servidor. Revisa la IP en API_URL, que Flask esté corriendo y que el celular esté en la misma red WiFi."
        );
      } else {
        setError(e.message);
      }
    } finally {
      clearTimeout(temporizador);
      setCargando(false);
    }
  }

  const pct = (x) => (x * 100).toFixed(1);

  return (
    <ScrollView contentContainerStyle={styles.contenedor}>
      <Text style={styles.titulo}>¿Perro o gato?</Text>
      <Text style={styles.subtitulo}>Cliente móvil · imagen en base64 hacia el servicio Flask</Text>

      <View style={styles.fila}>
        <Pressable style={styles.boton} onPress={tomarFoto}>
          <Text style={styles.textoBoton}>📷 Tomar foto</Text>
        </Pressable>
        <Pressable style={[styles.boton, styles.botonSecundario]} onPress={elegirDeGaleria}>
          <Text style={[styles.textoBoton, styles.textoSecundario]}>🖼️ Galería</Text>
        </Pressable>
      </View>

      {imagen && (
        <>
          <Image source={{ uri: imagen.uri }} style={styles.imagen} resizeMode="cover" />
          <Pressable
            style={[styles.boton, styles.botonVerde, cargando && styles.botonDeshabilitado]}
            onPress={clasificar}
            disabled={cargando}
          >
            {cargando ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.textoBoton}>Clasificar</Text>
            )}
          </Pressable>
        </>
      )}

      {!!error && (
        <View style={styles.cajaError}>
          <Text style={styles.textoError}>{error}</Text>
        </View>
      )}

      {resultado && (
        <View style={styles.resultado}>
          <Text style={styles.claseResultado}>
            {resultado.prediccion.clase} ({pct(resultado.prediccion.confianza)}%)
          </Text>

          {Object.entries(resultado.prediccion.probabilidades).map(([clase, p]) => (
            <View key={clase} style={{ marginBottom: 8 }}>
              <Text>
                {clase}: {pct(p)}%
              </Text>
              <View style={styles.barraFondo}>
                <View style={[styles.barraRelleno, { width: `${pct(p)}%` }]} />
              </View>
            </View>
          ))}

          <Text style={styles.meta}>
            Servidor: {resultado.tiempo_ms} ms · Cliente: {resultado.metadata.cliente} · Origen:{" "}
            {resultado.metadata.origen}
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenedor: {
    padding: 20,
    paddingTop: 60,
    paddingBottom: 48,
    backgroundColor: "#f4f6f8",
    flexGrow: 1,
  },
  titulo: { fontSize: 26, fontWeight: "700", color: "#1f2933" },
  subtitulo: { color: "#52606d", marginBottom: 16, marginTop: 4 },
  fila: { flexDirection: "row", gap: 10, marginBottom: 16 },
  boton: {
    backgroundColor: "#2563eb",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  botonSecundario: { backgroundColor: "#e4e7eb" },
  botonVerde: { backgroundColor: "#16a34a", marginTop: 12 },
  botonDeshabilitado: { opacity: 0.6 },
  textoBoton: { color: "white", fontWeight: "600", fontSize: 15 },
  textoSecundario: { color: "#1f2933" },
  imagen: { width: "100%", aspectRatio: 1, borderRadius: 12, backgroundColor: "#000" },
  cajaError: { backgroundColor: "#fde8e8", padding: 12, borderRadius: 8, marginTop: 14 },
  textoError: { color: "#9b1c1c" },
  resultado: {
    backgroundColor: "white",
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    elevation: 2,
  },
  claseResultado: {
    fontSize: 22,
    fontWeight: "700",
    textTransform: "capitalize",
    marginBottom: 10,
  },
  barraFondo: {
    height: 10,
    backgroundColor: "#e4e7eb",
    borderRadius: 5,
    overflow: "hidden",
    marginTop: 4,
  },
  barraRelleno: { height: "100%", backgroundColor: "#2563eb" },
  meta: { fontSize: 12, color: "#52606d", marginTop: 6 },
});