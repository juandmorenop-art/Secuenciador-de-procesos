import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la interfaz
st.set_page_config(page_title="Secuenciador de procesos", layout="wide")

# Mapeo de jerarquía de color para lavado de tinta
COLOR_VALOR = {
    'claro': 1, 'vainilla': 1, 'blanco': 1, 'amarillo': 1,
    'medio': 2, 'fresa': 2, 'arequipe': 2, 'naranja': 2,
    'oscuro': 3, 'chocolate': 3, 'café': 3, 'negro': 3
}

def obtener_nivel_color(texto_color):
    texto = str(texto_color).lower()
    for clave, val in COLOR_VALOR.items():
        if clave in texto:
            return val
    return 2

def calcular_costo_transicion(pedido_a, pedido_b, w_solvente, w_papel):
    col_a = obtener_nivel_color(pedido_a['Color Predominante'])
    col_b = obtener_nivel_color(pedido_b['Color Predominante'])
    
    if col_b < col_a:
        costo_solvente = 15.0
        tiempo_lavado = 45.0
    elif col_b > col_a:
        costo_solvente = 3.0
        tiempo_lavado = 15.0
    else:
        costo_solvente = 1.0
        tiempo_lavado = 5.0

    ancho_a = float(pedido_a['Ancho Bobina (mm)'])
    ancho_b = float(pedido_b['Ancho Bobina (mm)'])
    diff_ancho = abs(ancho_a - ancho_b)
    
    merma_papel = (diff_ancho / 1000.0) * 15.0
    tiempo_ancho = (diff_ancho / 50.0) * 10.0

    costo_total = (w_solvente * costo_solvente) + (w_papel * merma_papel)
    tiempo_total = tiempo_lavado + tiempo_ancho

    return costo_total, costo_solvente, merma_papel, tiempo_total

def optimizar_secuencia(df, peso_solv, peso_pap):
    n = len(df)
    if n == 0:
        return df, 0, 0, 0, 0, 0, 0

    w_s = peso_solv / 100.0
    w_p = peso_pap / 100.0

    no_visitados = list(range(n))
    inicio = min(no_visitados, key=lambda i: obtener_nivel_color(df.iloc[i]['Color Predominante']))
    
    secuencia = [inicio]
    no_visitados.remove(inicio)

    costo_solv_opt, merma_pap_opt, tiempo_opt = 0.0, 0.0, 0.0
    actual = inicio

    while no_visitados:
        siguiente_mejor = None
        costo_min = float('inf')
        metricas_mejor = (0, 0, 0)

        for cand in no_visitados:
            c_tot, c_sol, m_pap, t_seg = calcular_costo_transicion(
                df.iloc[actual], df.iloc[cand], w_s, w_p
            )
            if c_tot < costo_min:
                costo_min = c_tot
                siguiente_mejor = cand
                metricas_mejor = (c_sol, m_pap, t_seg)

        secuencia.append(siguiente_mejor)
        costo_solv_opt += metricas_mejor[0]
        merma_pap_opt += metricas_mejor[1]
        tiempo_opt += metricas_mejor[2]
        
        actual = siguiente_mejor
        no_visitados.remove(siguiente_mejor)

    costo_solv_emp, merma_pap_emp, tiempo_emp = 0.0, 0.0, 0.0
    for i in range(n - 1):
        _, c_s, m_p, t_s = calcular_costo_transicion(df.iloc[i], df.iloc[i+1], w_s, w_p)
        costo_solv_emp += c_s
        merma_pap_emp += m_p
        tiempo_emp += t_s

    df_opt = df.iloc[secuencia].reset_index(drop=True)
    df_opt.index = df_opt.index + 1

    return df_opt, costo_solv_opt, merma_pap_opt, tiempo_opt, costo_solv_emp, merma_pap_emp, tiempo_emp

# Interfaz
st.title("📊 PROGRAMADOR DE SECUENCIAS")
st.markdown("Modelo matemático de **Programación Dinámica / TSP** para reducción de lavado y desalineación.")

st.sidebar.title("⚙️ Panel de Control")
archivo_subido = st.sidebar.file_uploader("Subir Pedidos en Excel (.xlsx)", type=["xlsx", "csv"])

st.sidebar.markdown("---")
st.sidebar.markdown("### Parámetros de Optimización")
peso_solvente = st.sidebar.slider("Prioridad: Ahorro de Solvente (%)", 0, 100, 50)
peso_papel = 100 - peso_solvente
st.sidebar.info(f"Prioridad Ahorro de Papel: **{peso_papel}%**")

btn_optimizar = st.sidebar.button("🚀 Generar Secuencia Óptima", width="stretch")

if archivo_subido is not None:
    try:
        if archivo_subido.name.endswith('.csv'):
            df_pedidos = pd.read_csv(archivo_subido)
        else:
            df_pedidos = pd.read_excel(archivo_subido)
        st.sidebar.success("✅ ¡Excel cargado con éxito!")
    except Exception as e:
        st.sidebar.error(f"Error al leer el archivo: {e}")
        df_pedidos = pd.DataFrame()
else:
    df_pedidos = pd.DataFrame({
        'ID Pedido': ['OP-101', 'OP-102', 'OP-103', 'OP-104', 'OP-105', 'OP-106'],
        'Producto': ['Cono 100ml', 'Cono 250ml', 'Vaso 1L', 'Cono 100ml', 'Vaso 500ml', 'Cono 250ml'],
        'Ancho Bobina (mm)': [800, 800, 1000, 950, 1000, 800],
        'Color Predominante': ['Claro (Vainilla)', 'Oscuro (Chocolate)', 'Medio (Fresa)', 'Claro (Vainilla)', 'Oscuro (Chocolate)', 'Oscuro (Café)'],
        'Metros a Cortar': [5000, 3500, 8000, 4000, 6000, 3000]
    })

if btn_optimizar and not df_pedidos.empty:
    df_res, c_solv, m_pap, t_opt, c_solv_emp, m_pap_emp, t_emp = optimizar_secuencia(
        df_pedidos, peso_solvente, peso_papel
    )
    
    red_solv = ((c_solv_emp - c_solv) / c_solv_emp * 100) if c_solv_emp > 0 else 0
    red_pap = ((m_pap_emp - m_pap) / m_pap_emp * 100) if m_pap_emp > 0 else 0
    red_t = t_emp - t_opt

    st.success("¡Secuencia optimizada calculada en tiempo real!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💧 Solvente Estimado", f"{c_solv:.1f} L", f"-{red_solv:.1f}% vs Empírico")
    col2.metric("📜 Merma de Papel", f"{m_pap:.1f} Kg", f"-{red_pap:.1f}% vs Empírico")
    col3.metric("⏱️ Tiempo de Setup (M/G/1)", f"{t_opt:.0f} Min", f"-{red_t:.0f} Min ahorrados")
    
    st.divider()
    st.subheader("📋 Secuencia Reordenada para Planta")
    st.dataframe(df_res, width="stretch")
else:
    st.info("👈 Carga un archivo Excel o usa la tabla base, luego haz clic en **'Generar Secuencia Óptima'**.")
    st.write("Lista de pedidos cargada actualmente:")
    st.dataframe(df_pedidos, width="stretch")
