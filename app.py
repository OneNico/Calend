import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime
from pathlib import Path

# --- 0. CARGA DE TAILWIND Y ESTILOS PERSONALIZADOS ---
st.markdown("<script src='https://cdn.tailwindcss.com'></script>", unsafe_allow_html=True)
css = Path("styles.css").read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Gestión de Mantenciones",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CARGA DE DATOS ---
@st.cache_data(ttl=300)
def load_data_from_google_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
        ).worksheet("Hoja 1")
        df = pd.DataFrame(sheet.get_all_records())
        if 'fecha' in df.columns:
            df['fecha_dt'] = pd.to_datetime(df['fecha'], format='%d-%m-%y', errors='coerce')
        else:
            st.error("No se encontró la columna 'fecha'.")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

# --- 3. FUNCIONES AUXILIARES ---
def update_task_status_in_sheets(task_id, status, completion_date=None):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
        ).worksheet("Hoja 1")
        cell = sheet.find(str(task_id), in_column=1)
        if not cell:
            st.error(f"ID {task_id} no encontrado.")
            return False
        sheet.update_cell(cell.row, 7, status)
        if completion_date:
            sheet.update_cell(cell.row, 8, completion_date.strftime('%d-%m-%y'))
        return True
    except Exception as e:
        st.error(f"Error al actualizar: {e}")
        return False

def get_task_status(task):
    hoy = datetime.now().date()
    fecha = task['fecha_dt'].date() if pd.notna(task['fecha_dt']) else None
    if task.get('estado') == 'Completada':
        return "Completada"
    if fecha and fecha < hoy:
        return "Vencida"
    return "Pendiente"

def calculate_metrics(df):
    total = len(df)
    completadas = df[df['estado']=='Completada'].shape[0]
    vencidas = df[(df['estado']!='Completada') & (df['fecha_dt'].dt.date < datetime.now().date())].shape[0]
    pendientes = total - completadas - vencidas
    return {'total': total, 'completadas': completadas, 'vencidas': vencidas, 'pendientes': pendientes}

def create_charts(df):
    eng = df['ingeniero'].value_counts()
    fig_eng = px.bar(x=eng.values, y=eng.index, orientation='h', title="Tareas por Ingeniero")
    fig_eng.update_layout(height=350, template="streamlit")
    m = calculate_metrics(df)
    status_df = pd.DataFrame({
        'Estado': ['Completadas','Vencidas','Pendientes'],
        'Cantidad': [m['completadas'], m['vencidas'], m['pendientes']]
    })
    fig_status = px.pie(status_df, values='Cantidad', names='Estado', title="Distribución de Estados")
    fig_status.update_layout(height=350, template="streamlit")
    return fig_eng, fig_status

# --- 4. INTERFAZ PRINCIPAL ---
def main():
    df = load_data_from_google_sheet()
    if df.empty:
        return

    # Header
    st.markdown("""
    <div class="header-container">
      <h1 class="text-4xl font-bold">🔧 Sistema de Gestión de Mantenciones</h1>
      <p class="text-gray-500 mt-2">Monitoreo y control de tareas de mantenimiento – 2025</p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["📋 Tareas", "📊 Dashboard", "✅ Registro"])
    # TAB 1
    with tabs[0]:
        pendientes = [r.to_dict() for _,r in df.iterrows() if get_task_status(r) != "Completada"]
        if not pendientes:
            st.markdown('<div class="custom-alert alert-info">✅ No hay tareas pendientes.</div>', unsafe_allow_html=True)
        else:
            for t in pendientes:
                st.markdown('<div class="task-card">', unsafe_allow_html=True)
                cols = st.columns([4,2,1])
                with cols[0]:
                    fecha = t['fecha_dt'].strftime('%d/%m/%Y') if pd.notna(t['fecha_dt']) else "N/A"
                    st.markdown(f"<p class='font-semibold text-lg'>{t['cliente']}</p><p class='text-sm text-gray-500'>📅 {fecha} • 👤 {t['ingeniero']} • 🛠️ {t['tipo']}</p>", unsafe_allow_html=True)
                with cols[1]:
                    estado = get_task_status(t)
                    cls = estado.lower()
                    icon = "🚨" if estado=="Vencida" else "⏰"
                    st.markdown(f"<span class='status-badge status-{cls}'>{icon} {estado}</span>", unsafe_allow_html=True)
                with cols[2]:
                    if st.button("Hecho", key=f"btn_{t['id']}"):
                        if update_task_status_in_sheets(t['id'], "Completada", datetime.now().date()):
                            st.experimental_rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # TAB 2
    with tabs[1]:
        m = calculate_metrics(df)
        c1,c2,c3,c4 = st.columns(4)
        for col, label, val, color in [
            (c1, "Total", m['total'], "text-gray-800"),
            (c2, "Completadas", m['completadas'], "text-green-600"),
            (c3, "Pendientes", m['pendientes'], "text-yellow-600"),
            (c4, "Vencidas", m['vencidas'], "text-red-600"),
        ]:
            col.markdown(f"""
              <div class="metric-card">
                <p class="text-3xl font-bold {color}">{val}</p>
                <p class="mt-1 text-sm text-gray-500">{label}</p>
              </div>
            """, unsafe_allow_html=True)
        if m['vencidas']>0:
            st.markdown('<div class="custom-alert alert-warning">⚠️ Hay tareas vencidas.</div>', unsafe_allow_html=True)
        fig_e, fig_s = create_charts(df)
        st.plotly_chart(fig_s, use_container_width=True)
        st.plotly_chart(fig_e, use_container_width=True)

    # TAB 3
    with tabs[2]:
        comp = df[df['estado']=="Completada"].sort_values('fecha_dt', ascending=False)
        if comp.empty:
            st.markdown('<div class="custom-alert alert-info">ℹ️ No hay tareas completadas aún.</div>', unsafe_allow_html=True)
        else:
            for _,t in comp.iterrows():
                st.markdown('<div class="task-card">', unsafe_allow_html=True)
                cols = st.columns([4,1])
                with cols[0]:
                    fecha = t['fecha_dt'].strftime('%d/%m/%Y')
                    st.markdown(f"<p class='font-semibold'>{t['cliente']}</p><p class='text-sm text-gray-500'>📅 {fecha}</p>", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown("<span class='status-badge status-completada'>✅ Completada</span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
