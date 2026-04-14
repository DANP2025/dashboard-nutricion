# Comandos para subir a GitHub

## Paso 1: Crear el repositorio en GitHub
1. Ve a https://github.com y crea un nuevo repositorio llamado `dashboard-nutricion-profesional`
2. NO añadas README, .gitignore o license (ya los tenemos)
3. Copia la URL del repositorio (HTTPS o SSH)

## Paso 2: Conectar el repositorio local con GitHub
```bash
# Reemplaza TU_USERNAME con tu nombre de usuario de GitHub
git remote add origin https://github.com/TU_USERNAME/dashboard-nutricion-profesional.git

# O si prefieres SSH:
# git remote add origin git@github.com:TU_USERNAME/dashboard-nutricion-profesional.git
```

## Paso 3: Subir los archivos al repositorio
```bash
# Cambiar a la rama main (si tu GitHub usa main por defecto)
git branch -M main

# Subir los archivos al repositorio remoto
git push -u origin main
```

## Paso 4: Verificar que todo esté correcto
```bash
# Ver el estado del repositorio
git status

# Ver los commits
git log --oneline

# Ver los remotos configurados
git remote -v
```

## Notas importantes:
- El archivo `.streamlit/secrets.toml` está ignorado por seguridad
- Deberás configurar las credenciales manualmente en GitHub si necesitas despliegue
- Los archivos de entorno virtual también están ignorados
- La carpeta `streamlit` está lista para ser desplegada en cualquier plataforma

## Para futuros cambios:
```bash
# Añadir cambios
git add .

# Hacer commit
git commit -m "Descripción del cambio"

# Subir cambios
git push origin main
```
