import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime as dt

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Dashboard Nutrición", page_icon="🥗")

# ── CSS global ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Tarjeta de filtros */
    .filtros-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 16px;
    }

    /* Chips de multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #1a3a5c !important;
        border-radius: 6px !important;
    }

    /* Gráficos con tarjeta */
    [data-testid="stPlotlyChart"] {
        background: white;
        border-radius: 12px;
        padding: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }

    /* Botón refrescar */
    .stButton > button {
        background-color: #1a3a5c;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 24px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #2c5f8a;
        color: white;
    }

    /* Título de sección de gráficos */
    .chart-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1a3a5c;
        margin-bottom: 4px;
        padding-left: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def conectar_google_sheets():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        # Verificar que los secrets estén disponibles
        if "gcp_service_account" not in st.secrets:
            st.error("Error: No se encontraron las credenciales de Google Cloud en st.secrets")
            st.error("Por favor configura las credenciales en los secrets de Streamlit Cloud")
            return None
        
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        return gspread.authorize(creds)
    except KeyError as e:
        st.error(f"Error: Falta configuración de secrets: {e}")
        st.error("Por favor configura las credenciales en los secrets de Streamlit Cloud")
        return None
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        return None


@st.cache_data(ttl=300)
def cargar_datos():
    client = conectar_google_sheets()
    if client is None:
        return None
    try:
        spreadsheet = client.open("Base_datos_nutricion")
        worksheet = spreadsheet.worksheet("Nutricion")

        # CORRECCIÓN CLAVE: usar UNFORMATTED_VALUE para obtener números reales
        # sin formato de Google Sheets (evita valores inflados por formato de celda)
        data = worksheet.get_all_records(
            value_render_option='UNFORMATTED_VALUE',
            date_time_render_option='FORMATTED_STRING'
        )

        if not data:
            st.error("La hoja de cálculo está vacía o no tiene datos")
            return None

        df = pd.DataFrame(data)

        # Convertir fecha
        df["Fecha de Eval."] = pd.to_datetime(df["Fecha de Eval."], errors="coerce")

        # Convertir columnas numéricas con limpieza defensiva
        cols_excluir = {"Fecha de Eval.", "Jugador", "Posicion"}
        for col in df.columns:
            if col not in cols_excluir:
                try:
                    # Reemplazar coma decimal europea si el valor es string
                    df[col] = df[col].apply(
                        lambda x: str(x).replace(',', '.') if isinstance(x, str) else x
                    )
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception:
                    pass

        # ── Validación de rangos conocidos (red de seguridad) ────────────────
        # Si algún valor supera el máximo fisiológicamente posible,
        # se reemplaza por NaN para no distorsionar los gráficos
        rangos_validos = {
            "Sum 6 plieg.":        (0, 300),    # mm: máximo razonable ~250mm
            "OBJTIVO SUM PLIEGUES": (0, 300),
            "%GRASA YUHASZ":       (0, 50),     # %: máximo razonable ~40%
            "OBJETIVO YUHASZ":     (0, 50),
            "M adiposa a bajar":   (-30, 30),   # kg: rango razonable
            "M musc a aumentar":   (-30, 30),   # kg: rango razonable
            "Plieg 1":             (0, 80),
            "Plieg 2":             (0, 80),
            "Plieg 3":             (0, 80),
            "Plieg 4":             (0, 80),
            "Plieg 5":             (0, 80),
            "Plieg 6":             (0, 80),
        }

        for col, (vmin, vmax) in rangos_validos.items():
            if col in df.columns:
                mask_invalido = (df[col] < vmin) | (df[col] > vmax)
                if mask_invalido.any():
                    n_invalidos = mask_invalido.sum()
                    st.warning(
                        f"⚠️ Columna '{col}': se detectaron {n_invalidos} valor(es) "
                        f"fuera del rango esperado [{vmin}, {vmax}] y fueron ignorados."
                    )
                    df.loc[mask_invalido, col] = None

        # Traducir meses a español
        meses_es = {
            "January": "Enero", "February": "Febrero", "March": "Marzo",
            "April": "Abril", "May": "Mayo", "June": "Junio",
            "July": "Julio", "August": "Agosto", "September": "Septiembre",
            "October": "Octubre", "November": "Noviembre", "December": "Diciembre",
        }
        df["Mes/Año"] = df["Fecha de Eval."].dt.strftime("%B %Y")
        for eng, esp in meses_es.items():
            df["Mes/Año"] = df["Mes/Año"].str.replace(eng, esp)

        return df

    except gspread.SpreadsheetNotFound:
        st.error("Error: No se encontró el spreadsheet 'Base_datos_nutricion'")
        return None
    except gspread.WorksheetNotFound:
        st.error("Error: No se encontró la hoja 'Nutricion'")
        return None
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None


# ── Gráfico de pequeños múltiplos ────────────────────────────────────────────
def crear_grafico_multiples(df, col_actual, col_objetivo, titulo,
                             ytitle, color_actual="#e63946", color_obj="#2a9d8f"):
    """
    Crea un gráfico de barras agrupadas con un subplot (pequeño múltiplo)
    por cada mes, ordenados cronológicamente.
    """
    # Ordenar meses cronológicamente
    orden_meses = (
        df[["Mes/Año", "Fecha de Eval."]]
        .dropna()
        .drop_duplicates("Mes/Año")
        .sort_values("Fecha de Eval.")["Mes/Año"]
        .tolist()
    )

    n_meses = len(orden_meses)
    if n_meses == 0:
        return None

    # ── Calcular rango Y real sobre los datos filtrados ──────────────────────
    vals_actual = pd.to_numeric(df[col_actual], errors="coerce").dropna()
    vals_obj    = pd.to_numeric(df[col_objetivo], errors="coerce").dropna()
    
    if vals_actual.empty and vals_obj.empty:
        return None

    y_max_real = max(
        vals_actual.max() if not vals_actual.empty else 0,
        vals_obj.max()    if not vals_obj.empty    else 0,
    )
    # Agregar 25% de margen para que las etiquetas no se corten
    y_range = [0, round(y_max_real * 1.30, 1)]

    fig = make_subplots(
        rows=1,
        cols=n_meses,
        shared_yaxes=False,          # ← CAMBIO CLAVE: cada subplot maneja su propio eje
        subplot_titles=orden_meses,
        horizontal_spacing=0.06,
    )

    show_legend = True

    for i, mes in enumerate(orden_meses, start=1):
        df_mes = df[df["Mes/Año"] == mes].copy()
        jugadores = df_mes["Jugador"].tolist()

        # Nombres descriptivos para la leyenda
        if col_actual == "M adiposa a bajar":
            name_actual   = "Adiposa a bajar"
            name_objetivo = "Muscular a aumentar"
        else:
            name_actual   = col_actual
            name_objetivo = "Objetivo"

        # Valores numéricos seguros
        y_actual = pd.to_numeric(df_mes[col_actual],  errors="coerce").round(1)
        y_obj    = pd.to_numeric(df_mes[col_objetivo], errors="coerce").round(1)

        # Barra: valor actual
        fig.add_trace(
            go.Bar(
                x=jugadores,
                y=y_actual,
                name=name_actual,
                marker_color=color_actual,
                text=[f"{v:.1f}" if pd.notna(v) else "" for v in y_actual],
                textposition="inside",
                textfont=dict(size=10, color="white"),
                showlegend=show_legend,
                legendgroup="actual",
                cliponaxis=False,
            ),
            row=1, col=i,
        )

        # Barra: objetivo
        fig.add_trace(
            go.Bar(
                x=jugadores,
                y=y_obj,
                name=name_objetivo,
                marker_color=color_obj,
                text=[f"{v:.1f}" if pd.notna(v) else "" for v in y_obj],
                textposition="inside",
                textfont=dict(size=10, color="white"),
                showlegend=show_legend,
                legendgroup="objetivo",
                cliponaxis=False,
            ),
            row=1, col=i,
        )

        show_legend = False

        # ── Aplicar rango Y fijo en cada subplot ────────────────────────────
        yaxis_key = "yaxis" if i == 1 else f"yaxis{i}"
        fig.layout[yaxis_key].update(
            range=y_range,
            gridcolor="#f0f0f0",
            tickformat=".1f",
            showgrid=True,
        )

    fig.update_layout(
        barmode="group",
        height=420,
        margin=dict(t=50, b=70, l=40, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#dee2e6",
            borderwidth=1,
        ),
    )

    # Rotar etiquetas del eje X
    fig.update_xaxes(tickangle=-40, tickfont=dict(size=9))

    # Subtítulos de meses
    for ann in fig.layout.annotations:
        ann.update(font=dict(size=12, color="#1a3a5c"))

    return fig


# ── Gráfico de radar ─────────────────────────────────────────────────────────
def crear_grafico_radar(df_jugador, df_equipo):
    pliegues = ["Plieg 1", "Plieg 2", "Plieg 3", "Plieg 4", "Plieg 5", "Plieg 6"]
    disp = [p for p in pliegues if p in df_jugador.columns]
    if not disp:
        return None

    vals_j = [float(df_jugador[p].iloc[0]) if pd.notna(df_jugador[p].iloc[0]) else 0 for p in disp]
    vals_e = [df_equipo[p].mean() if p in df_equipo.columns else 0 for p in disp]

    # Cerrar polígono
    vals_j.append(vals_j[0])
    vals_e.append(vals_e[0])
    cats = disp + [disp[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_j, theta=cats, fill="toself", name="Jugador",
        line_color="#1a3a5c", fillcolor="rgba(26,58,92,0.2)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals_e, theta=cats, fill="toself", name="Promedio Equipo",
        line_color="#e63946", fillcolor="rgba(230,57,70,0.15)"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True,
            range=[0, max(max(vals_j), max(vals_e)) * 1.15])),
        height=500,
        margin=dict(t=40, b=20, l=30, r=30),
        legend=dict(orientation="h", y=-0.12),
        paper_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=11),
    )
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    # ── Encabezado ──────────────────────────────────────────────────────────
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.image("punto_referencia.png")
    st.title("Dashboard de Nutrición Profesional")
    st.caption("Monitoreo y seguimiento de composición corporal")

    # ── Cargar datos ─────────────────────────────────────────────────────────
    df = cargar_datos()
    if df is None or df.empty:
        st.error("No se pudieron cargar los datos del Google Sheet.")
        return

    # ── Filtros dentro del dashboard ─────────────────────────────────────────
    st.markdown('<div class="filtros-card">', unsafe_allow_html=True)
    st.markdown("**🔍 Filtros de análisis**")

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        posiciones = sorted(df["Posicion"].dropna().unique().tolist())
        posicion_sel = st.multiselect(
            "🏃 Posición", options=posiciones, default=posiciones,
            placeholder="Todas las posiciones..."
        )

    with col_f2:
        # Ordenar meses cronológicamente (por fecha real, no alfabético)
        orden_ref = (
            df[["Mes/Año", "Fecha de Eval."]]
            .dropna()
            .drop_duplicates("Mes/Año")
            .sort_values("Fecha de Eval.")
        )
        meses_disponibles = orden_ref["Mes/Año"].tolist()
        meses_sel = st.multiselect(
            "📅 Mes / Año", options=meses_disponibles,
            default=[meses_disponibles[-1]] if meses_disponibles else [],
            placeholder="Seleccionar mes(es)..."
        )

    with col_f3:
        jugadores = sorted(df["Jugador"].dropna().unique().tolist())
        jugadores_sel = st.multiselect(
            "👤 Jugador", options=jugadores, default=jugadores,
            placeholder="Todos los jugadores..."
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Aplicar filtros ───────────────────────────────────────────────────────
    df_f = df.copy()
    if posicion_sel:
        df_f = df_f[df_f["Posicion"].isin(posicion_sel)]
    if meses_sel:
        df_f = df_f[df_f["Mes/Año"].isin(meses_sel)]
    if jugadores_sel:
        df_f = df_f[df_f["Jugador"].isin(jugadores_sel)]

    if df_f.empty:
        st.warning("⚠️ No hay datos con los filtros seleccionados.")
        return

    # ── Gráficos principales ─────────────────────────────────────────────────
    st.markdown('<div class="chart-title">📊 Sumatoria 6 Pliegues vs Objetivo</div>',
                unsafe_allow_html=True)
    if "Sum 6 plieg." in df_f.columns and "OBJTIVO SUM PLIEGUES" in df_f.columns:
        fig1 = crear_grafico_multiples(
            df_f, "Sum 6 plieg.", "OBJTIVO SUM PLIEGUES",
            "Pliegues vs Objetivo", "mm"
        )
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("Columnas de pliegues no encontradas.")

    st.divider()

    st.markdown('<div class="chart-title">📊 % Grasa Yuhasz vs Objetivo</div>',
                unsafe_allow_html=True)
    if "%GRASA YUHASZ" in df_f.columns and "OBJETIVO YUHASZ" in df_f.columns:
        fig2 = crear_grafico_multiples(
            df_f, "%GRASA YUHASZ", "OBJETIVO YUHASZ",
            "% Grasa vs Objetivo", "%"
        )
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Columnas de % grasa no encontradas.")

    st.divider()

    st.markdown('<div class="chart-title">📊 Composición Corporal</div>',
                unsafe_allow_html=True)
    if "M musc a aumentar" in df_f.columns and "M adiposa a bajar" in df_f.columns:
        fig3 = crear_grafico_multiples(
            df_f, "M adiposa a bajar", "M musc a aumentar",
            "Composición Corporal", "Masa (kg)",
            color_actual="#e63946", color_obj="#2a9d8f"
        )
        if fig3:
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("Columnas de composición no encontradas.")

    # ── Radar (primer jugador seleccionado) ──────────────────────────────────
    if jugadores_sel:
        jugador_radar = jugadores_sel[0]
        df_jugador = df_f[df_f["Jugador"] == jugador_radar]
        if not df_jugador.empty:
            st.markdown("---")
            st.markdown(f'<div class="chart-title">🕸️ Perfil de Pliegues: {jugador_radar}</div>',
                        unsafe_allow_html=True)
            fig_radar = crear_grafico_radar(df_jugador, df_f)
            if fig_radar:
                st.plotly_chart(fig_radar, use_container_width=True)

    # ── Controles de refresco ─────────────────────────────────────────────────
    st.markdown("---")
    col_btn, col_timer = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Refrescar Datos"):
            st.cache_data.clear()
            st.rerun()

    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = dt.now()

    elapsed = (dt.now() - st.session_state.last_refresh).total_seconds()
    if elapsed > 300:
        st.session_state.last_refresh = dt.now()
        st.cache_data.clear()
        st.rerun()

    with col_timer:
        remaining = max(0, int(300 - elapsed))
        st.caption(f"⏱️ Próximo refresco automático en {remaining} segundos")


if __name__ == "__main__":
    main()
