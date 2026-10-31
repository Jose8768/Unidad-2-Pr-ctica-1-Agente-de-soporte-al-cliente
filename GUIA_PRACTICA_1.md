# Guía de Práctica 1: Mi Primer Agente de IA con Python y Gemini 3.8

---

## Objetivo
Construir y ejecutar un agente inteligente en Python que:
1. Conecte de forma automatizada con una hoja de cálculo de Google Sheets (vinculada a un Google Form de quejas y sugerencias).
2. Lea los registros pendientes de procesamiento.
3. Se comunique con la API de Google Gemini (gemini-3.8-flash) para clasificar la queja (Ventas, Soporte Técnico o Logística) y detectar el sentimiento (Positivo, Negativo o Neutro).
4. Escriba los resultados y marque la fila con "SI" en la columna Agente Ejecutado.

---

## Requisitos Técnicos y Cuentas
* Cuenta de Google (Gmail).
* Python 3.9 o superior instalado.
* Editor de código (Visual Studio Code recomendado).
* Conexión a Internet.

---

## Procedimiento de Implementación

### Fase 1: Formulario y Base de Datos (Google Forms y Sheets)

1. **Crear el Formulario**:
   * Ingresar a https://forms.google.com con la cuenta de Google.
   * Asignar el título: "Formulario de Quejas y Sugerencias".
   * Pregunta 1: "Tu Nombre" (tipo Respuesta corta, campo opcional).
   * Pregunta 2: "Describe tu queja, sugerencia o comentario" (tipo Párrafo, campo obligatorio).
2. **Vincular la Hoja de Cálculo (Google Sheets)**:
   * En el formulario, hacer clic en la pestaña "Respuestas".
   * Hacer clic en el icono verde de Google Sheets y seleccionar "Crear una nueva hoja de cálculo".
   * Nombrarla con la cadena exacta: "Respuestas de Quejas (Base de Datos)".
3. **Completar las Columnas de la Hoja**:
   * Las columnas A, B y C se generan de forma automática:
     * Columna A: Marca temporal
     * Columna B: Tu Nombre
     * Columna C: Describe tu queja...
   * Agregar manualmente los siguientes encabezados en las columnas consecutivas:
     * Columna D: Clasificación IA
     * Columna E: Sentimiento IA
     * Columna F: Agente Ejecutado
4. **Registrar un Registro de Prueba**:
   * Abrir la vista previa del formulario y enviar:
     * Nombre: Cliente de Prueba
     * Comentario: Mi pedido llegó tarde y la caja estaba rota. Muy mal servicio.
   * Confirmar la recepción del dato en las columnas A, B y C de Google Sheets.

---

### Fase 2: Configurar Acceso a Google Sheets (OAuth 2.0)

1. Ingresar a https://console.cloud.google.com con la cuenta de Gmail.
2. **Crear Proyecto**:
   * En el selector superior, hacer clic en "Proyecto nuevo".
   * Asignar el nombre: Agente de Soporte y hacer clic en Crear.
   * Seleccionar el proyecto creado en la barra superior.
3. **Habilitar APIs**:
   * Ir a APIs y servicios -> Biblioteca.
   * Buscar "Google Sheets API" y presionar "Habilitar".
   * Regresar a la Biblioteca, buscar "Google Drive API" y presionar "Habilitar".
4. **Pantalla de Consentimiento OAuth**:
   * Ir a APIs y servicios -> Pantalla de consentimiento de OAuth.
   * Seleccionar tipo de usuario: External -> Crear.
   * Completar los campos obligatorios:
     * Nombre de la aplicación: AgenteSoporte
     * Correo electrónico de asistencia: Correo del usuario
     * Correo de contacto del desarrollador: Correo del usuario
   * Guardar y continuar hasta finalizar el asistente.
5. **Configurar Usuario de Prueba**:
   * En la misma sección de consentimiento, localizar la sección "Audience" -> "Test users".
   * Hacer clic en "+ Add Users" e ingresar el correo propio de Gmail.
   * Guardar los cambios (requisito indispensable para evitar el error 403 access_denied).
6. **Generar Credenciales**:
   * Ir a APIs y servicios -> Credenciales.
   * Clic en "+ Crear credenciales" -> "ID de cliente de OAuth 2.0".
   * Tipo de aplicación: "Aplicación de escritorio" (Desktop app).
   * Nombre: agente-soporte -> Crear.
   * En el cuadro de diálogo, hacer clic en "Descargar JSON".
   * Renombrar el archivo descargado a client_secrets.json y colocarlo en el directorio de la práctica.

---

### Fase 3: Obtener la API Key de Gemini

1. Ingresar a https://aistudio.google.com/app/api-keys.
2. Hacer clic en "Create API key".
3. Seleccionar el proyecto de Google Cloud creado previamente (Agente de Soporte).
4. Copiar la clave generada (cadena iniciada con "AIzaSy...").

---

### Fase 4: Instalación de Dependencias y Ejecución

1. Abrir la terminal en este directorio e instalar los requerimientos:
   ```bash
   pip install -r requirements.txt
   ```
2. Configurar la clave de Gemini:
   * Opción recomendada: Copiar el archivo .env.example como .env y definir la clave:
     ```env
     GEMINI_API_KEY=AIzaSyTuClaveReal...
     GEMINI_MODEL=gemini-3.8-flash
     ```
   * Opción alternativa: Editar directamente la variable GEMINI_API_KEY dentro de agente_soporte.py.
3. Ejecutar el script:
   ```bash
   python agente_soporte.py
   ```
4. **Flujo de Primera Autorización**:
   * El sistema abrirá automáticamente una ventana del navegador web solicitando permisos.
   * En la advertencia "Google no verificó esta app", hacer clic en "Configuración avanzada" -> "Ir a AgenteSoporte (no seguro)" -> "Continuar".
   * La terminal confirmará la conexión y procesará la fila inicial.

---

### Fase 5: Pruebas y Validación

1. Con el script en ejecución, enviar tres registros de prueba desde el formulario:
   * **Caso 1**:
     * Nombre: Ana
     * Comentario: No entiendo cómo funciona la nueva app, el botón de ayuda no sirve.
     * Resultado esperado: Soporte Técnico / Negativo
   * **Caso 2**:
     * Nombre: Carlos
     * Comentario: Me atendió un vendedor llamado Juan y fue increíble, ¡resolvió todo! 10/10.
     * Resultado esperado: Ventas / Positivo
   * **Caso 3**:
     * Nombre: María
     * Comentario: Mi paquete lleva 2 semanas sin llegar y nadie me da información.
     * Resultado esperado: Logística / Negativo
2. Verificar en la salida de terminal que el agente detecta cada comentario, realiza la invocación a Gemini y actualiza la hoja.
3. Confirmar en Google Sheets que las columnas D, E y F contienen la clasificación, el sentimiento y la marca "SI".
4. Para finalizar la ejecución interactiva en terminal, presionar Ctrl + C.

---

### Fase 6: Control de Versiones con Git

Para respaldar el proyecto en GitHub de forma segura:
1. En GitHub, crear un repositorio vacío denominado `practica1-agente-python`.
2. En la terminal del directorio actual, ejecutar:
   ```bash
   git init
   git add .
   git status  # Verificar que .env y client_secrets.json estén excluidos
   git commit -m "Practica 1: Implementacion de agente de soporte con Gemini 3.8"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/practica1-agente-python.git
   git push -u origin main
   ```

---

## Evidencias para Entrega
1. Captura de pantalla de la terminal con el script procesando las filas.
2. Captura de pantalla de Google Sheets con las columnas D, E y F completadas.
3. Captura de pantalla de Google Cloud Console con las APIs habilitadas.

---

## Solución de Problemas Comunes

| Error | Causa Raíz | Solución |
| :--- | :--- | :--- |
| FileNotFoundError: client_secrets.json | El archivo descargado no reside en la raíz del script o tiene otro nombre. | Renombrar a client_secrets.json exactamente y validar su ubicación. |
| Error 403: access_denied | La cuenta de Gmail no está registrada en usuarios de prueba. | En Cloud Console -> OAuth consent screen -> Test users, registrar el correo propio. |
| SpreadsheetNotFound | El nombre de la hoja difiere del valor configurado en NOMBRE_HOJA. | Verificar concordancia exacta de caracteres, mayúsculas y espacios. |
| API key not valid (Gemini) | Clave mal copiada o con espacios en blanco. | Reemitir la clave en AI Studio y copiarla sin caracteres adicionales. |
