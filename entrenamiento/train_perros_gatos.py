import os
import zipfile
import urllib.request

import keras
from keras import layers
from tensorflow import data as tf_data

# ---------- 0. Configuración ----------
EPOCHS = 15            # En Colab con GPU: 15 está bien. En CPU, prueba con 3.
IMAGE_SIZE = (180, 180)
BATCH_SIZE = 128

# Trabajar siempre desde la carpeta del script (no aplica en notebooks de Colab)
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    pass

# Si existe ../servidor, guarda el modelo allá; si no (Colab), en la carpeta actual
RUTA_SALIDA = "../servidor/modelos" if os.path.isdir("../servidor") else "."

# ---------- 1. Descargar datos ----------
URL = "https://download.microsoft.com/download/3/E/1/3E1C3F21-ECDB-4869-8368-6DEBA77B919F/kagglecatsanddogs_5340.zip"
ZIP = "kagglecatsanddogs_5340.zip"

if not os.path.exists("PetImages"):
    print("Descargando dataset (786 MB)...")
    urllib.request.urlretrieve(URL, ZIP)
    with zipfile.ZipFile(ZIP) as z:
        z.extractall(".")
    print("Dataset listo.")

# ---------- 2. Eliminar imágenes corruptas ----------
num_skipped = 0
for folder_name in ("Cat", "Dog"):
    folder_path = os.path.join("PetImages", folder_name)
    for fname in os.listdir(folder_path):
        fpath = os.path.join(folder_path, fname)
        try:
            fobj = open(fpath, "rb")
            is_jfif = b"JFIF" in fobj.peek(10)
        finally:
            fobj.close()
        if not is_jfif:
            num_skipped += 1
            os.remove(fpath)
print(f"Imágenes eliminadas: {num_skipped}")

# ---------- 3. Datasets ----------
train_ds, val_ds = keras.utils.image_dataset_from_directory(
    "PetImages",
    validation_split=0.2,
    subset="both",
    seed=1337,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)
# Etiquetas: Cat = 0, Dog = 1 (orden alfabético)

# ---------- 4. Aumento de datos (solo para entrenamiento) ----------
data_augmentation_layers = [
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
]

def data_augmentation(images):
    for layer in data_augmentation_layers:
        images = layer(images)
    return images

train_ds = train_ds.map(
    lambda img, label: (data_augmentation(img), label),
    num_parallel_calls=tf_data.AUTOTUNE,
)
train_ds = train_ds.prefetch(tf_data.AUTOTUNE)
val_ds = val_ds.prefetch(tf_data.AUTOTUNE)

# ---------- 5. Modelo (mini Xception) ----------
def make_model(input_shape, num_classes):
    inputs = keras.Input(shape=input_shape)

    x = layers.Rescaling(1.0 / 255)(inputs)   # el modelo mismo normaliza
    x = layers.Conv2D(128, 3, strides=2, padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)

    previous_block_activation = x

    for size in [256, 512, 728]:
        x = layers.Activation("relu")(x)
        x = layers.SeparableConv2D(size, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.Activation("relu")(x)
        x = layers.SeparableConv2D(size, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.MaxPooling2D(3, strides=2, padding="same")(x)

        residual = layers.Conv2D(size, 1, strides=2, padding="same")(
            previous_block_activation
        )
        x = layers.add([x, residual])
        previous_block_activation = x

    x = layers.SeparableConv2D(1024, 3, padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)

    x = layers.GlobalAveragePooling2D()(x)
    units = 1 if num_classes == 2 else num_classes
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(units, activation=None)(x)  # logits
    return keras.Model(inputs, outputs)

model = make_model(input_shape=IMAGE_SIZE + (3,), num_classes=2)

# ---------- 6. Entrenar ----------
model.compile(
    optimizer=keras.optimizers.Adam(3e-4),
    loss=keras.losses.BinaryCrossentropy(from_logits=True),
    metrics=[keras.metrics.BinaryAccuracy(name="acc")],
)

model.fit(train_ds, epochs=EPOCHS, validation_data=val_ds)

# ---------- 7. Guardar ----------
os.makedirs(RUTA_SALIDA, exist_ok=True)
destino = os.path.join(RUTA_SALIDA, "perros_gatos.keras")
model.save(destino)
print(f"Modelo guardado en: {os.path.abspath(destino)}")