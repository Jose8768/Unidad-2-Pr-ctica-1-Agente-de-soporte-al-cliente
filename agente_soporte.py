"""
================================================================================
PRÁCTICA 1: MI PRIMER AGENTE DE IA
Construcción de un Agente de Soporte con Python y Gemini
================================================================================
Descripción:
Este script lee automáticamente quejas o sugerencias registradas en un
Google Form (almacenadas en Google Sheets), las envía al modelo Gemini 3.8 Flash
para su análisis de sentimiento y clasificación por departamento, y registra
el resultado en tiempo real de vuelta en la hoja de cálculo.
================================================================================
"""

import json
import os
import time
import schedule
import gspread
from google import genai
from google.genai import types

# Cargar variables de entorno si existe archivo .env local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==============================================================================
# SECCIÓN DE CONFIGURACIÓN
# ==============================================================================
# Nombre del archivo JSON de credenciales OAuth 2.0 descargado de Google Cloud Console
ARCHIVO_CREDENCIALES = "client_secrets.json"

# Nombre exacto de tu hoja de cálculo vinculada al Google Form (respetar mayúsculas y espacios)
NOMBRE_HOJA = "Respuestas de Quejas (Base de Datos)"

# Modelo de IA de última generación
MODELO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Tu API Key de Gemini obtenida en Google AI Studio (https://aistudio.google.com/app/api-keys)
# Puedes colocarla en tu archivo .env o escribirla directamente aquí si no lo subes a Git:
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "TU_GEMINI_API_KEY_AQUI")

# Cada cuántos minutos el agente revisará la hoja en busca de quejas nuevas
INTERVALO_MINUTOS = 15

# Constantes numéricas para las columnas en Google Sheets (1-based: A=1, B=2, C=3, ...)
COL_NOMBRE = 2         # Columna B: Tu Nombre
COL_COMENTARIO = 3     # Columna C: Describe tu queja...
COL_CLASIFICACION = 4  # Columna D: Clasificación IA (Ventas / Soporte Técnico / Logística)
COL_SENTIMIENTO = 5    # Columna E: Sentimiento IA (Positivo / Negativo / Neutro)
COL_EJECUTADO = 6      # Columna F: Agente Ejecutado ('SI')


# ==============================================================================
# FUNCIÓN: CONECTAR CON GOOGLE SHEETS
# ==============================================================================
def conectar_sheets():
    """
    Autentica el script con Google Sheets usando OAuth 2.0 a través de gspread.
    La primera vez abrirá el navegador para autorizar el acceso.
    Retorna el objeto de la primera hoja (sheet1).
    """
    try:
        # Autenticación con OAuth 2.0 usando el archivo client_secrets.json
        gc = gspread.oauth(credentials_filename=ARCHIVO_CREDENCIALES)
        # Abrir la hoja por su nombre exacto
        hoja_calculo = gc.open(NOMBRE_HOJA)
        # Retornar la primera hoja de trabajo
        return hoja_calculo.sheet1
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a Google Sheets: {e}")
        return None


# ==============================================================================
# FUNCIÓN: ANALIZAR CON GEMINI AI
# ==============================================================================
def analizar_con_gemini(comentario: str) -> dict:
    """
    Envía el comentario del cliente al modelo Gemini 3.8 Flash.
    Utiliza GenerateContentConfig con instrucción de sistema para garantizar
    una respuesta estrictamente estructurada en formato JSON puro.
    Retorna un diccionario Python con 'clasificacion' y 'sentimiento'.
    """
    prompt_usuario = (
        f"Analiza la siguiente queja, sugerencia o comentario de un cliente:\n\n"
        f"\"{comentario}\"\n\n"
        f"Devuelve un objeto JSON con exactamente dos claves:\n"
        f"- \"clasificacion\": Debe ser exactamente una de estas tres opciones: \"Ventas\", \"Soporte Técnico\" o \"Logística\".\n"
        f"- \"sentimiento\": Debe ser exactamente una de estas tres opciones: \"Positivo\", \"Negativo\" o \"Neutro\"."
    )

    config = types.GenerateContentConfig(
        system_instruction=(
            "Eres un analista de soporte al cliente experto. Tu única tarea es clasificar "
            "comentarios de clientes y detectar su sentimiento. Debes responder ÚNICAMENTE "
            "con un objeto JSON válido con las claves 'clasificacion' y 'sentimiento', "
            "sin explicaciones adicionales, sin saludos y sin texto introductorio."
        ),
        response_mime_type="application/json",
        temperature=0.1
    )

    respuesta = cliente_gemini.models.generate_content(
        model=MODELO_GEMINI,
        contents=prompt_usuario,
        config=config
    )

    # Limpieza preventiva en caso de formato markdown
    texto_respuesta = respuesta.text.strip()
    if texto_respuesta.startswith("```json"):
        texto_respuesta = texto_respuesta[7:]
    elif texto_respuesta.startswith("```"):
        texto_respuesta = texto_respuesta[3:]
    if texto_respuesta.endswith("```"):
        texto_respuesta = texto_respuesta[:-3]
    texto_respuesta = texto_respuesta.strip()

    # Convertir el texto JSON a un diccionario Python
    datos_analisis = json.loads(texto_respuesta)
    return datos_analisis


# ==============================================================================
# FUNCIÓN: AGENTE PRINCIPAL
# ==============================================================================
def ejecutar_agente():
    """
    Orquesta el ciclo de vida del agente:
    1. Conecta con Google Sheets.
    2. Lee todas las filas existentes.
    3. Filtra aquellas que no hayan sido procesadas (Columna F vacía).
    4. Analiza cada queja con Gemini.
    5. Escribe la clasificación, sentimiento y 'SI' en Google Sheets.
    """
    print("\n" + "=" * 55)
    print("[AGENTE] Iniciando ciclo de revisión de Google Sheets...")
    print("=" * 55)

    # 1. Conectar con la hoja
    hoja = conectar_sheets()
    if hoja is None:
        print("[!] Terminando ciclo debido a fallas de conexión con Google Sheets.")
        return False

    # 2. Leer todas las filas
    try:
        filas = hoja.get_all_values()
    except Exception as e:
        print(f"[ERROR] Error al leer los datos de la hoja de cálculo: {e}")
        return False

    # Si solo hay 1 fila (o ninguna), solo están los encabezados
    if len(filas) <= 1:
        print("[i] No se encontraron registros de clientes en la hoja aún.")
        return True

    # 3. Filtrar y procesar filas nuevas
    filas_datos = filas[1:] # Omitimos encabezados
    nuevas_procesadas = 0
    ya_procesadas = 0

    # enumerate con start=2 porque la fila 1 es encabezado y Google Sheets es 1-based
    for indice_fila, fila in enumerate(filas_datos, start=2):
        # Verificar estado en la Columna F (Agente Ejecutado)
        estado_f = fila[COL_EJECUTADO - 1].strip().upper() if len(fila) >= COL_EJECUTADO else ""

        if estado_f == "SI":
            ya_procesadas += 1
            continue

        # Extraer nombre y queja
        nombre = fila[COL_NOMBRE - 1].strip() if len(fila) >= COL_NOMBRE and fila[COL_NOMBRE - 1].strip() else "Anónimo"
        comentario = fila[COL_COMENTARIO - 1].strip() if len(fila) >= COL_COMENTARIO else ""

        if not comentario:
            print(f"[!] Fila {indice_fila}: Comentario vacío, se omite.")
            continue

        print(f"\n[+] Queja detectada de: {nombre} (Fila {indice_fila})")
        print(f"    Comentario: \"{comentario}\"")

        # 4. Analizar con Gemini
        try:
            resultado = analizar_con_gemini(comentario)
            clasificacion = resultado.get("clasificacion", "Desconocido")
            sentimiento = resultado.get("sentimiento", "Neutro")

            print(f"    -> Clasificación IA: {clasificacion}")
            print(f"    -> Sentimiento IA:   {sentimiento}")

            # 5. Escribir resultados en Google Sheets
            hoja.update_cell(indice_fila, COL_CLASIFICACION, clasificacion)
            hoja.update_cell(indice_fila, COL_SENTIMIENTO, sentimiento)
            hoja.update_cell(indice_fila, COL_EJECUTADO, "SI")
            print(f"    [OK] Fila {indice_fila} actualizada en Google Sheets con éxito.")
            nuevas_procesadas += 1

        except Exception as e:
            # Tolerancia a fallos: no detenemos el agente si una fila falla
            print(f"    [ERROR] No se pudo procesar la fila {indice_fila}: {e}")
            print("    [!] La fila continuará pendiente para el próximo ciclo.")

    print("\n" + "-" * 55)
    print(f"Resumen del ciclo: {nuevas_procesadas} quejas nuevas procesadas | {ya_procesadas} quejas ya atendidas.")
    print("-" * 55)
    return True


# ==============================================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("      AGENTE DE SOPORTE AUTOMATIZADO (PYTHON + GEMINI 3.8)     ")
    print("=" * 65)

    # 1. Validación de la API Key de Gemini
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TU_GEMINI_API_KEY_AQUI" or "Ejemplo" in GEMINI_API_KEY:
        print("\n[ERROR CRÍTICO] Debes configurar tu GEMINI_API_KEY.")
        print("Obtén tu clave gratuita en: https://aistudio.google.com/app/api-keys")
        print("Puedes colocarla en el archivo .env o en la variable GEMINI_API_KEY.\n")
        exit(1)

    # 2. Validación del archivo de credenciales de Google Sheets
    if not os.path.exists(ARCHIVO_CREDENCIALES):
        print(f"\n[ERROR CRÍTICO] No se encontró el archivo '{ARCHIVO_CREDENCIALES}'.")
        print("Descarga tus credenciales OAuth 2.0 (Desktop app) desde Google Cloud Console,")
        print(f"renómbralo exactamente a '{ARCHIVO_CREDENCIALES}' y colócalo junto a este script.\n")
        exit(1)

    # 3. Inicialización del cliente de Gemini
    print(f"[*] Inicializando cliente de Google Gemini ({MODELO_GEMINI})...")
    cliente_gemini = genai.Client(api_key=GEMINI_API_KEY)

    # 4. Ejecución inmediata inicial
    print("[*] Ejecutando revisión inicial de la hoja...")
    ejecutar_agente()

    # 5. Programar ejecuciones automáticas periódicas
    print(f"\n[*] Agente configurado para revisar la hoja cada {INTERVALO_MINUTOS} minutos.")
    print("[*] Presiona Ctrl + C en cualquier momento para detener el agente.\n")
    schedule.every(INTERVALO_MINUTOS).minutes.do(ejecutar_agente)

    # 6. Bucle de mantenimiento en ejecución
    while True:
        schedule.run_pending()
        time.sleep(30)
