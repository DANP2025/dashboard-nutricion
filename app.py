import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
import datetime
from datetime import datetime as dt

# Configuración de la página
st.set_page_config(layout="wide", page_title="Dashboard Nutrición")

# Función para conectar a Google Sheets
def conectar_google_sheets():
    try:
        # Verificar que los secrets estén disponibles
        if "gcp_service_account" not in st.secrets:
            st.error("Error: No se encontraron las credenciales de Google Cloud en st.secrets")
            return None
        
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        
        # Crear credenciales con diagnóstico
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes
            )
        except Exception as cred_error:
            st.error(f"Error creando credenciales: {cred_error}")
            st.error("Verifica que todos los campos en secrets.toml estén correctos")
            return None
        
        # Autorizar cliente gspread
        try:
            client = gspread.authorize(creds)
            return client
        except Exception as auth_error:
            st.error(f"Error autorizando gspread: {auth_error}")
            st.error("Verifica que la Service Account tenga los permisos correctos")
            return None
            
    except Exception as e:
        st.error(f"Error general conectando a Google Sheets: {e}")
        return None

# Función para cargar datos
def cargar_datos():
    client = conectar_google_sheets()
    if client is None:
        return None
    
    try:
        # Abrir el spreadsheet usando URL completa
        try:
            # URL del Google Sheet nativo - NUEVA URL
            spreadsheet_url = "https://docs.google.com/spreadsheets/d/1Q1k4G55SiT0YDIBE5SFT0ktap16zsvv8sDszmL5Br2Y/edit"
            
            # Intentar usar URL completa primero
            try:
                if "TU_SPREADSHEET_ID" not in spreadsheet_url:
                    # Usar URL completa
                    spreadsheet = client.open_by_url(spreadsheet_url)
                    st.success("Conexión exitosa al Google Sheet por URL")
                else:
                    raise ValueError("URL no configurada")
            except:
                # Fallback: usar nombre del spreadsheet
                spreadsheet = client.open("Base_datos_nutricion")
                st.success("Conexión exitosa al Google Sheet 'Base_datos_nutricion'")
        except Exception as sheet_error:
            st.error(f"Error abriendo Google Sheet 'Base_datos_nutricion': {sheet_error}")
            st.error("Verifica que:")
            st.error("1. El Google Sheet 'Base_datos_nutricion' exista")
            st.error("2. La Service Account tenga acceso al documento")
            st.error("3. El nombre del documento sea exactamente 'Base_datos_nutricion'")
            return None
        
        # Buscar la pestaña 'Nutricion'
        try:
            worksheet = spreadsheet.worksheet("Nutricion")
            st.success("Pestaña 'Nutricion' encontrada exitosamente")
        except Exception as worksheet_error:
            st.error(f"Error encontrando pestaña 'Nutricion': {worksheet_error}")
            st.error("Verifica que:")
            st.error("1. La pestaña 'Nutricion' exista en el documento")
            st.error("2. El nombre de la pestaña sea exactamente 'Nutricion'")
            # Mostrar pestañas disponibles para diagnóstico
            try:
                worksheets = spreadsheet.worksheets()
                available_sheets = [ws.title for ws in worksheets]
                st.error(f"Pestañas disponibles: {available_sheets}")
            except:
                pass
            return None
        
        # Obtener datos
        try:
            data = worksheet.get_all_records()
            if not data:
                st.error("La pestaña 'Nutricion' está vacía o no tiene datos")
                return None
            
            df = pd.DataFrame(data)
            st.success(f"Datos cargados exitosamente: {len(df)} filas")
            
        except Exception as data_error:
            st.error(f"Error obteniendo datos de la pestaña: {data_error}")
            st.error("Verifica que la primera fila tenga encabezados")
            return None
        
        # Convertir 'Fecha de Eval.' a datetime
        try:
            df['Fecha de Eval.'] = pd.to_datetime(df['Fecha de Eval.'], errors='coerce')
            
            # Crear columna 'Mes/Año'
            df['Mes/Año'] = df['Fecha de Eval.'].dt.strftime('%B %Y')
            
            # Traducir meses a español si es necesario
            meses_es = {
                'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
                'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
                'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
                'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
            }
            
            for eng, esp in meses_es.items():
                df['Mes/Año'] = df['Mes/Año'].str.replace(eng, esp)
            
            return df
            
        except Exception as process_error:
            st.error(f"Error procesando fechas: {process_error}")
            st.error("Verifica que exista la columna 'Fecha de Eval.'")
            return None
            
    except Exception as e:
        st.error(f"Error general cargando datos: {e}")
        return None

# Función para obtener colores según condición
def obtener_color_por_condicion(valor, objetivo):
    if valor <= objetivo:
        return 'green'
    else:
        return 'red'

# Función para obtener color composición
def obtener_color_composicion(valor):
    if valor > 0:
        return 'red'
    else:
        return 'green'

# Función principal
def main():
    # Título e imagen de referencia
    st.title("Dashboard de Nutrición")
    
    # Mostrar imagen punto_referencia.png centrada
    try:
        st.image("punto_referencia.png", width=400, use_container_width=True)
    except:
        st.warning("No se encontró la imagen punto_referencia.png")
    
    # Cargar datos
    df = cargar_datos()
    
    if df is None or df.empty:
        st.error("No se pudieron cargar los datos del Google Sheet")
        return
    
    # Barra lateral con filtros
    st.sidebar.header("Filtros")
    
    # Obtener valores únicos para filtros
    posiciones = df['Posicion'].dropna().unique().tolist()
    meses_anio = sorted(df['Mes/Año'].dropna().unique().tolist())
    jugadores = df['Jugador'].dropna().unique().tolist()
    
    # Filtros dinámicos
    posicion_selected = st.sidebar.multiselect(
        "Posición",
        options=posiciones,
        default=posiciones
    )
    
    mes_anio_selected = st.sidebar.multiselect(
        "Mes/Año",
        options=meses_anio,
        default=meses_anio
    )
    
    jugador_selected = st.sidebar.multiselect(
        "Jugador",
        options=jugadores,
        default=jugadores
    )
    
    # Filtrar datos según selección
    df_filtrado = df.copy()
    
    if posicion_selected:
        df_filtrado = df_filtrado[df_filtrado['Posicion'].isin(posicion_selected)]
    
    if mes_anio_selected:
        df_filtrado = df_filtrado[df_filtrado['Mes/Año'].isin(mes_anio_selected)]
    
    if jugador_selected:
        df_filtrado = df_filtrado[df_filtrado['Jugador'].isin(jugador_selected)]
    
    if df_filtrado.empty:
        st.warning("No hay datos con los filtros seleccionados")
        return
    
    # Crear gráficos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Pliegues")
        
        # Gráfico 1: Pliegues
        fig1 = go.Figure()
        
        # Agregar barras de Sum 6 plieg
        colores_pliegues = []
        for idx, row in df_filtrado.iterrows():
            if pd.notna(row['Sum 6 plieg.']) and pd.notna(row['OBJTIVO SUM PLIEGUES']):
                color = obtener_color_por_condicion(row['Sum 6 plieg.'], row['OBJTIVO SUM PLIEGUES'])
                colores_pliegues.append(color)
            else:
                colores_pliegues.append('blue')
        
        fig1.add_trace(go.Bar(
            x=df_filtrado['Jugador'],
            y=df_filtrado['Sum 6 plieg.'],
            name='Sum 6 plieg',
            marker_color=colores_pliegues,
            text=df_filtrado['Sum 6 plieg.'],
            textposition='auto'
        ))
        
        # Agregar barra de objetivo
        fig1.add_trace(go.Bar(
            x=df_filtrado['Jugador'],
            y=df_filtrado['OBJTIVO SUM PLIEGUES'],
            name='Objetivo',
            marker_color='black',
            text=df_filtrado['OBJTIVO SUM PLIEGUES'],
            textposition='auto'
        ))
        
        fig1.update_layout(
            title="Pliegues vs Objetivo",
            xaxis_title="Jugador",
            yaxis_title="Valor",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("% Grasa")
        
        # Gráfico 2: % Grasa
        fig2 = go.Figure()
        
        # Agregar barras de %GRASA YUHASZ
        colores_grasa = []
        for idx, row in df_filtrado.iterrows():
            if pd.notna(row['%GRASA YUHASZ']) and pd.notna(row['OBJETIVO YUHASZ']):
                color = obtener_color_por_condicion(row['%GRASA YUHASZ'], row['OBJETIVO YUHASZ'])
                colores_grasa.append(color)
            else:
                colores_grasa.append('blue')
        
        fig2.add_trace(go.Bar(
            x=df_filtrado['Jugador'],
            y=df_filtrado['%GRASA YUHASZ'],
            name='% Grasa',
            marker_color=colores_grasa,
            text=df_filtrado['%GRASA YUHASZ'],
            textposition='auto'
        ))
        
        # Agregar barra de objetivo
        fig2.add_trace(go.Bar(
            x=df_filtrado['Jugador'],
            y=df_filtrado['OBJETIVO YUHASZ'],
            name='Objetivo',
            marker_color='black',
            text=df_filtrado['OBJETIVO YUHASZ'],
            textposition='auto'
        ))
        
        fig2.update_layout(
            title="% Grasa vs Objetivo",
            xaxis_title="Jugador",
            yaxis_title="Valor (%)",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    with col3:
        st.subheader("Composición Corporal")
        
        # Gráfico 3: Composición
        fig3 = go.Figure()
        
        # Colores para composición
        colores_muscular = [obtener_color_composicion(val) if pd.notna(val) else 'blue' 
                           for val in df_filtrado['M musc a aumentar']]
        colores_adiposa = [obtener_color_composicion(val) if pd.notna(val) else 'blue' 
                          for val in df_filtrado['M adiposa a bajar']]
        
        fig3.add_trace(go.Bar(
            x=df_filtrado['Jugador'],
            y=df_filtrado['M musc a aumentar'],
            name='M. Musc. a aumentar',
            marker_color=colores_muscular,
            text=df_filtrado['M musc a aumentar'],
            textposition='auto'
        ))
        
        fig3.add_trace(go.Bar(
            x=df_filtrado['Jugador'],
            y=df_filtrado['M adiposa a bajar'],
            name='M. Adiposa a bajar',
            marker_color=colores_adiposa,
            text=df_filtrado['M adiposa a bajar'],
            textposition='auto'
        ))
        
        fig3.update_layout(
            title="Composición Corporal",
            xaxis_title="Jugador",
            yaxis_title="Valor (kg)",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig3, use_container_width=True)
    
    # Tabla de datos filtrados
    st.subheader("Datos Detallados")
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Botón para refrescar datos
    if st.button("Refrescar Datos"):
        st.rerun()
    
    # Refresco automático cada 5 minutos
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = dt.now()
    
    current_time = dt.now()
    time_diff = (current_time - st.session_state.last_refresh).total_seconds()
    
    if time_diff > 300:  # 5 minutos = 300 segundos
        st.session_state.last_refresh = current_time
        st.rerun()
    
    # Mostrar tiempo hasta próximo refresco
    remaining_time = 300 - time_diff
    st.caption(f"Próximo refresco automático en: {int(remaining_time)} segundos")

if __name__ == "__main__":
    main()
