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
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        return None

# Función para cargar datos
def cargar_datos():
    client = conectar_google_sheets()
    if client is None:
        return None
    
    try:
        # Abrir el spreadsheet 'Base_datos_nutricion'
        spreadsheet = client.open("Base_datos_nutricion")
        worksheet = spreadsheet.worksheet("Nutricion")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Convertir 'Fecha de Eval.' a datetime
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
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
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
