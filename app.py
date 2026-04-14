import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
import datetime
from datetime import datetime as dt

# Configuración de la página
st.set_page_config(layout="wide", page_title="Dashboard Nutrición", page_icon=":bar_chart:")

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

# Función para crear gráfico de barras Actual vs Objetivo
def crear_grafico_comparacion(df_actual, df_objetivo, titulo, y_title, nombre_actual, nombre_objetivo):
    fig = go.Figure()
    
    # Barra actual (Rojo)
    fig.add_trace(go.Bar(
        x=df_actual['Jugador'],
        y=df_actual[nombre_actual],
        name='Actual',
        marker_color='red',
        text=df_actual[nombre_actual],
        textposition='auto',
        texttemplate='%{y:.1f}'
    ))
    
    # Barra objetivo (Verde)
    fig.add_trace(go.Bar(
        x=df_objetivo['Jugador'],
        y=df_objetivo[nombre_objetivo],
        name='Objetivo',
        marker_color='green',
        text=df_objetivo[nombre_objetivo],
        textposition='auto',
        texttemplate='%{y:.1f}'
    ))
    
    fig.update_layout(
        title=titulo,
        xaxis_title="Jugador",
        yaxis_title=y_title,
        barmode='group',
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Función para crear gráfico de radar
def crear_grafico_radar(df_jugador, df_equipo):
    fig = go.Figure()
    
    # Pliegues disponibles
    pliegues = ['Plieg 1', 'Plieg 2', 'Plieg 3', 'Plieg 4', 'Plieg 5', 'Plieg 6']
    
    # Filtrar columnas de pliegues que existen
    pliegues_disponibles = [p for p in pliegues if p in df_jugador.columns]
    
    if not pliegues_disponibles:
        return None
    
    # Datos del jugador
    valores_jugador = [df_jugador[p].iloc[0] if pd.notna(df_jugador[p].iloc[0]) else 0 for p in pliegues_disponibles]
    
    # Datos del equipo (promedio)
    valores_equipo = []
    for p in pliegues_disponibles:
        if p in df_equipo.columns:
            valores_equipo.append(df_equipo[p].mean())
        else:
            valores_equipo.append(0)
    
    # Cerrar el gráfico de radar
    valores_jugador.append(valores_jugador[0])
    valores_equipo.append(valores_equipo[0])
    pliegues_disponibles.append(pliegues_disponibles[0])
    
    # Añadir traza del jugador
    fig.add_trace(go.Scatterpolar(
        r=valores_jugador,
        theta=pliegues_disponibles,
        fill='toself',
        name='Jugador',
        line_color='blue',
        fillcolor='rgba(0, 123, 255, 0.25)'
    ))
    
    # Añadir traza del equipo
    fig.add_trace(go.Scatterpolar(
        r=valores_equipo,
        theta=pliegues_disponibles,
        fill='toself',
        name='Promedio Equipo',
        line_color='orange',
        fillcolor='rgba(255, 165, 0, 0.25)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max(valores_jugador), max(valores_equipo)) * 1.1]
            )
        ),
        title="Comparación de Pliegues: Jugador vs Equipo",
        height=500
    )
    
    return fig

# Función principal
def main():
    # Logo y título en contenedor
    with st.container():
        col1, col2, col1 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("punto_referencia.png", width=300)
            except:
                st.warning("No se encontró la imagen punto_referencia.png")
        
        st.title("Dashboard de Nutrición Profesional")
        st.markdown("---")
    
    # Cargar datos
    df = cargar_datos()
    
    if df is None or df.empty:
        st.error("No se pudieron cargar los datos del Google Sheet")
        return
    
    # Filtros superiores con st.pills
    with st.container():
        st.subheader("Filtros")
        
        # Obtener posiciones únicas
        posiciones = df['Posicion'].dropna().unique().tolist()
        if not posiciones:
            posiciones = ['Todas']
        
        # Selector de posición con pills
        posicion_seleccionada = st.pills(
            "Seleccionar Posición",
            options=posiciones,
            selection_mode="multi",
            default=posiciones[:1] if posiciones else []
        )
        
        # Obtener meses únicos
        meses_disponibles = sorted(df['Mes/Año'].dropna().unique().tolist())
        if meses_disponibles:
            mes_seleccionado = st.selectbox(
                "Seleccionar Mes",
                options=meses_disponibles,
                index=len(meses_disponibles) - 1 if meses_disponibles else 0
            )
        else:
            mes_seleccionado = None
        
        # Obtener jugadores únicos
        jugadores_disponibles = df['Jugador'].dropna().unique().tolist()
        if jugadores_disponibles:
            jugador_seleccionado = st.selectbox(
                "Seleccionar Jugador",
                options=jugadores_disponibles
            )
        else:
            jugador_seleccionado = None
    
    # Filtrar datos
    df_filtrado = df.copy()
    
    if posicion_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['Posicion'].isin(posicion_seleccionada)]
    
    if mes_seleccionado:
        df_filtrado = df_filtrado[df_filtrado['Mes/Año'] == mes_seleccionado]
    
    if df_filtrado.empty:
        st.warning("No hay datos con los filtros seleccionados")
        return
    
    st.markdown("---")
    
    # Gráficos principales en contenedores
    with st.container():
        st.subheader("Análisis de Composición Corporal")
        
        # Gráfico 1: % Grasa vs Objetivo
        if '%GRASA YUHASZ' in df_filtrado.columns and 'OBJETIVO YUHASZ' in df_filtrado.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_grasa = crear_grafico_comparacion(
                    df_filtrado, df_filtrado,
                    "% Grasa Corporal vs Objetivo",
                    "% Grasa",
                    '%GRASA YUHASZ',
                    'OBJETIVO YUHASZ'
                )
                st.plotly_chart(fig_grasa, use_container_width=True)
            
            # Gráfico 2: Pliegues vs Objetivo
            with col2:
                if 'Sum 6 plieg.' in df_filtrado.columns and 'OBJTIVO SUM PLIEGUES' in df_filtrado.columns:
                    fig_pliegues = crear_grafico_comparacion(
                        df_filtrado, df_filtrado,
                        "Sumatoria de Pliegues vs Objetivo",
                        "Sumatoria (mm)",
                        'Sum 6 plieg.',
                        'OBJTIVO SUM PLIEGUES'
                    )
                    st.plotly_chart(fig_pliegues, use_container_width=True)
        else:
            st.error("No se encontraron las columnas necesarias para los gráficos de comparación")
    
    # Gráfico de Masa Adiposa y Muscular
    with st.container():
        st.subheader("Análisis de Masa Corporal")
        
        if 'M adiposa a bajar' in df_filtrado.columns and 'M musc a aumentar' in df_filtrado.columns:
            fig_masa = crear_grafico_comparacion(
                df_filtrado, df_filtrado,
                "Masa Adiposa vs Masa Muscular",
                "Masa (kg)",
                'M adiposa a bajar',
                'M musc a aumentar'
            )
            st.plotly_chart(fig_masa, use_container_width=True)
    
    # Gráfico de Radar para jugador seleccionado
    if jugador_seleccionado:
        with st.container():
            st.subheader(f"Análisis Detallado: {jugador_seleccionado}")
            
            # Datos del jugador seleccionado
            df_jugador = df_filtrado[df_filtrado['Jugador'] == jugador_seleccionado]
            
            if not df_jugador.empty:
                # Gráfico de radar
                fig_radar = crear_grafico_radar(df_jugador, df_filtrado)
                if fig_radar:
                    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Tabla de datos
    with st.container():
        st.subheader("Datos Detallados")
        st.dataframe(df_filtrado, use_container_width=True)
    
    # Botón de refresco
    if st.button("Refrescar Datos"):
        st.rerun()

if __name__ == "__main__":
    main()
