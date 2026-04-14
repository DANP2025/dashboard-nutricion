# Guía de Despliegue - Streamlit Cloud

## Paso 1: Acceder a Streamlit Cloud

1. Ve a: https://share.streamlit.io/
2. Haz clic en "Sign in" y conecta tu cuenta de GitHub
3. Autoriza el acceso a tus repositorios

## Paso 2: Crear Nueva Aplicación

1. Haz clic en "New app" (botón morado en la esquina superior derecha)
2. Configura los siguientes campos:

### **Configuración del Repositorio**
- **Repository**: `DANP2025/dashboard-nutricion`
- **Branch**: `main`
- **Main file path**: `streamlit/app.py`

### **Configuración Avanzada**
- **Python version**: `3.9` (o la más reciente disponible)
- **Dependencies**: Dejar en "Use requirements.txt"

## Paso 3: Configurar Secrets (Credenciales)

En la sección "Secrets", añade las siguientes credenciales de Google Cloud:

```toml
[gcp_service_account]
type = "service_account"
project_id = "TU_PROJECT_ID"
private_key_id = "TU_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nTU_PRIVATE_KEY_COMPLETO\n-----END PRIVATE KEY-----\n"
client_email = "TU_CLIENT_EMAIL@YOUR_PROJECT_ID.iam.gserviceaccount.com"
client_id = "TU_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/TU_CLIENT_EMAIL%40YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

### **Cómo obtener estos datos:**
1. Ve a Google Cloud Console
2. Crea una Service Account
3. Descarga el archivo JSON
4. Copia los valores al formato TOML arriba

## Paso 4: Despliegue

1. Haz clic en "Deploy!"
2. Espera unos minutos mientras Streamlit Cloud:
   - Instala las dependencias
   - Descarga tu código
   - Inicia la aplicación

## Paso 5: Verificación

Una vez desplegado, tu aplicación estará disponible en:
**URL**: https://dashboard-nutricion.streamlit.app

### **Qué verificar:**
- La imagen `punto_referencia.png` se muestra correctamente
- Los filtros (Posición, Mes/Año, Jugador) funcionan
- Los gráficos se actualizan al cambiar filtros
- Los colores de los gráficos siguen la lógica correcta

## Si hay errores:

### **Error de conexión a Google Sheets:**
- Verifica que las credenciales sean correctas
- Asegúrate que la Service Account tenga permisos para acceder al Google Sheet
- Comprueba que el Google Sheet 'Base_datos_nutricion' exista

### **Error de dependencias:**
- Verifica que `requirements.txt` esté correcto
- Revisa los logs en Streamlit Cloud

### **Error de imagen no encontrada:**
- Verifica que `punto_referencia.png` esté en la carpeta correcta

## Mantenimiento:

### **Para actualizar la aplicación:**
1. Haz cambios en tu código local
2. Sube los cambios a GitHub:
   ```bash
   git add .
   git commit -m "Descripción del cambio"
   git push origin main
   ```
3. Streamlit Cloud detectará los cambios y recargará automáticamente

### **Para actualizar credenciales:**
1. Ve a Streamlit Cloud
2. Edit settings de tu aplicación
3. Actualiza los secrets
4. La aplicación se reiniciará automáticamente

## Soporte:

- **Documentación de Streamlit Cloud**: https://docs.streamlit.io/streamlit-cloud
- **Repositorio del proyecto**: https://github.com/DANP2025/dashboard-nutricion
- **Archivo principal**: `streamlit/app.py`
