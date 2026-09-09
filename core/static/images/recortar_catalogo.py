import os
from PIL import Image, ImageFilter

# ==============================================================
# Lista de las 8 capturas de pantalla del catalogo (todas .png,
# revisa el arbol de tu proyecto: todas terminan en .png, no .jpg)
# ==============================================================
archivos_catalogo = {
    "Captura de pantalla 2026-08-16 161452.png": [
        "vestido_de_silla", "panoleta", "velos_para_techo", "mesas"
    ],
    "Captura de pantalla 2026-08-16 161514.png": [
        "aro", "baking_puerta_y_marco", "mesas_entorchadas", "numeros"
    ],
    "Captura de pantalla 2026-08-16 161504.png": [
        "letras", "silla_trono", "cilindros_blancos", "base_cuadra"
    ],
    "Captura de pantalla 2026-08-16 161442.png": [
        "cilindros_vidrio", "hiedra", "hiedra_blanca", "bola_tejida_madera"
    ],
    "Captura de pantalla 2026-08-16 161430.png": [
        "mariposa", "baul", "tapete_rojo", "tapete_verde"
    ],
    "Captura de pantalla 2026-08-16 161421.png": [
        "tapete_blanco", "tapete_lila", "tapete_negro", "torre_eiffel"
    ],
    "Captura de pantalla 2026-08-16 161403.png": [
        "quinceanero", "mesa_de_ruedas", "rodajas_de_madera", "caballete"
    ],
    "Captura de pantalla 2026-08-16 161340.png": [
        "silla", "mantel_blanco", "sobre_mantel", "camino_de_yute"
    ],
}

# ==============================================================
# Coordenadas de recorte (medidas sobre la plantilla real, en vez
# de valores genericos que cortaban los items o dejaban franjas
# de fondo). Cada tupla es (arriba, abajo) como % del alto total.
# ==============================================================
Y_BANDS = [
    (0.010, 0.225),   # fila 1
    (0.252, 0.482),   # fila 2
    (0.508, 0.728),   # fila 3
    (0.760, 0.990),   # fila 4
]
X0_RATIO = 0.075   # inicio horizontal (evita la franja de color izquierda)
X1_RATIO = 0.420   # fin horizontal (justo antes del texto/precio)

CARPETA_ORIGEN = "."                     # carpeta donde estan las capturas
CARPETA_DESTINO = "catalogo_productos"   # carpeta de salida
ESCALA = 4        # factor de aumento de resolucion (HD)
PADDING = 40       # margen blanco alrededor de cada item, en px (tras escalar)

os.makedirs(CARPETA_DESTINO, exist_ok=True)
print("Iniciando recorte de items...")

for archivo, nombres in archivos_catalogo.items():
    ruta = os.path.join(CARPETA_ORIGEN, archivo)
    if not os.path.exists(ruta):
        print(f"Archivo no encontrado (se salta): {ruta}")
        continue

    img = Image.open(ruta).convert("RGB")
    ancho, alto = img.size

    x0 = int(ancho * X0_RATIO)
    x1 = int(ancho * X1_RATIO)

    for (y_top, y_bottom), nombre in zip(Y_BANDS, nombres):
        y0 = int(alto * y_top)
        y1 = int(alto * y_bottom)

        recorte = img.crop((x0, y0, x1, y1))

        # --- Escalado de alta calidad (Lanczos) + enfoque leve ---
        w, h = recorte.size
        recorte_hd = recorte.resize((w * ESCALA, h * ESCALA), Image.LANCZOS)
        recorte_hd = recorte_hd.filter(
            ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3)
        )

        # --- Fondo blanco con margen (para catalogo web) ---
        lienzo = Image.new(
            "RGB",
            (recorte_hd.width + PADDING * 2, recorte_hd.height + PADDING * 2),
            "white",
        )
        lienzo.paste(recorte_hd, (PADDING, PADDING))

        ruta_salida = os.path.join(CARPETA_DESTINO, f"{nombre}.png")
        # PNG en vez de JPG: sin compresion con perdida, mejor calidad
        lienzo.save(ruta_salida, format="PNG")
        print(f"Creada: {ruta_salida}")

print("\n¡Proceso finalizado con éxito!")