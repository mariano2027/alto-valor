import io
import pandas as pd
import streamlit as st
import plotly.express as px

# Configuración profesional del dashboard
st.set_page_config(page_title="Corporate Credit Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("💼 Sistema Profesional de Análisis de Cuentas Corrientes")
st.markdown("---")

# Carga del Reporte Base
uploaded_file = st.file_uploader("📂 Cargue el archivo de Cuenta Corriente (Excel)", type=["xlsx", "xls"])

def procesar_datos(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    
    # Sanitización de datos financieros
    columnas_num = ["saldo", "diasencalle", "debe", "haber", "original"]
    for col in columnas_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
    # Regla de Negocio: Eliminar registros de control de sistemas (líneas vacías o de suma cero)
    df = df[df["texto"].notna() & (df["texto"].str.strip() != "")]
    
    # Clasificación Financiera por Tramos de Edad (Aging Loops)
    def asignar_tramo(dias):
        if dias <= 0: return "Al Día"
        elif dias <= 60: return "0-60 Días"
        elif dias <= 75: return "61-75 Días"
        elif dias <= 90: return "76-90 Días"
        else: return "Mayor a 90 Días"
        
    df["tramo_mora"] = df["diasencalle"].apply(asignar_tramo)
    return df

if uploaded_file is not None:
    df_base = procesar_datos(uploaded_file)
    
    # Pestañas profesionales del Sistema Financiero
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Ejecutivo & Riesgo", "🗂️ Consulta de Cuenta Corriente", "⚠️ Top 20 Clientes Críticos (>75 Días)"])
    
    # ==========================================
    # PESTAÑA 1: ANALISIS FINANCIERO EJECUTIVO
    # ==========================================
    with tab1:
        st.subheader("Indicadores Globales de Exposición")
        
        # Cálculos de KPI de morosidad
        total_cartera = df_base["saldo"].sum()
        mora_60 = df_base[df_base["diasencalle"] > 60]["saldo"].sum()
        mora_75 = df_base[df_base["diasencalle"] > 75]["saldo"].sum()
        mora_90 = df_base[df_base["diasencalle"] > 90]["saldo"].sum()
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Cartera de Crédito Total", f"$ {total_cartera:,.2f}")
        k2.metric("Mora Crítica > 60 Días", f"$ {mora_60:,.2f}", f"{(mora_60/total_cartera)*100:.1f}% del total", delta_color="inverse")
        k3.metric("Mora Crítica > 75 Días", f"$ {mora_75:,.2f}", f"{(mora_75/total_cartera)*100:.1f}% del total", delta_color="inverse")
        k4.metric("Mora Crítica > 90 Días", f"$ {mora_90:,.2f}", f"{(mora_90/total_cartera)*100:.1f}% del total", delta_color="inverse")
        
        st.markdown("---")
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("### ⏳ Matriz de Envejecimiento de Deuda (Aging Table)")
            df_aging = df_base.groupby("tramo_mora")["saldo"].sum().reset_index()
            fig_pie = px.pie(df_aging, values="saldo", names="tramo_mora", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.RdBu_r)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with g2:
            st.markdown("### 📈 Concentración del Riesgo (Top 10 Deudores)")
            df_top10 = df_base.groupby("ncliente")["saldo"].sum().nlargest(10).reset_index()
            fig_bar = px.bar(df_top10, x="saldo", y="ncliente", orientation="h", 
                             labels={"saldo": "Saldo Acumulado", "ncliente": "Cliente"},
                             color="saldo", color_continuous_scale="Reds")
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

    # ==========================================
    # PESTAÑA 2: CONSULTA Y FILTROS INTERACTIVOS
    # ==========================================
    with tab2:
        st.subheader("Buscador Dinámico Multicriterio")
        
        c_filt1, c_filt2, c_filt3 = st.columns(3)
        with c_filt1:
            filtro_clientes = st.multiselect("Filtrar por Cliente Corporativo:", sorted(df_base["ncliente"].unique()))
        with c_filt2:
            filtro_tramos = st.multiselect("Filtrar por Tramo de Vencimiento:", ["Al Día", "0-60 Días", "61-75 Días", "76-90 Días", "Mayor a 90 Días"])
        with c_filt3:
            buscar_comprobante = st.text_input("🔍 Buscar Comprobante / Recibo:")
            
        # Filtrado Dinámico de datos
        df_dinamico = df_base.copy()
        if filtro_clientes:
            df_dinamico = df_dinamico[df_dinamico["ncliente"].isin(filtro_clientes)]
        if filtro_tramos:
            df_dinamico = df_dinamico[df_dinamico["tramo_mora"].isin(filtro_tramos)]
        if buscar_comprobante:
            df_dinamico = df_dinamico[df_dinamico["texto"].str.contains(buscar_comprobante, case=False, na=False)]
            
        # Estilado Condicional para Auditoría
        def resaltar_vencidos(row):
            return ['background-color: #fee2e2; color: #991b1b' if row['diasencalle'] > 90 else '' for _ in row]
            
        st.dataframe(df_dinamico.style.apply(resaltar_vencidos, axis=1).format({
            "original": "$ {:,.2f}", "debe": "$ {:,.2f}", "haber": "$ {:,.2f}", "saldo": "$ {:,.2f}"
        }), use_container_width=True, height=400)
        
        # Exportador de Registros Filtrados
        out_dinamico = io.BytesIO()
        with pd.ExcelWriter(out_dinamico, engine="openpyxl") as w:
            df_dinamico.to_excel(w, index=False, sheet_name="Registros_Filtrados")
        st.download_button("📥 Exportar Selección a Excel", out_dinamico.getvalue(), "cuenta_corriente_personalizada.xlsx")

       # ==========================================
    # PESTAÑA 3: TOP 20 COMPROBANTES CRÍTICOS (>75 DÍAS)
    # ==========================================
    with tab3:
        st.subheader("🚨 Reporte Especial: Top 20 Comprobantes con Saldos > 75 Días")
        st.markdown("Este módulo aísla de forma automática los 20 documentos individuales más grandes que superan la barrera de los 75 días en la calle.")
        
        # Filtrar deudas de más de 75 días
        df_mas_75 = df_base[df_base["diasencalle"] > 75].copy()
        
        # Renombrar columnas para claridad del reporte sin agrupar
        df_comprobantes = df_mas_75[["cliente", "ncliente", "texto", "saldo", "diasencalle", "vencim"]].copy()
        df_comprobantes.columns = ["Código", "Cliente", "Detalle Comprobante", "Saldo Documento", "Días en Calle", "Vencimiento"]
        
        # Extraer estrictamente los 20 comprobantes individuales más altos
        df_top20_docs = df_comprobantes.nlargest(20, "Saldo Documento")
        
        if not df_top20_docs.empty:
            # Mostrar la tabla detallada factura por factura
            st.dataframe(df_top20_docs.style.background_gradient(cmap="Reds", subset=["Saldo Documento"]).format({
                "Saldo Documento": "$ {:,.2f}",
                "Días en Calle": "{:.0f} días"
            }), use_container_width=True)
            
            # Exportador dedicado
            out_top20_docs = io.BytesIO()
            with pd.ExcelWriter(out_top20_docs, engine="openpyxl") as w:
                df_top20_docs.to_excel(w, index=False, sheet_name="Top_20_Facturas_Criticas")
            st.download_button("📥 Descargar Reporte de Documentos Críticos", out_top20_docs.getvalue(), "top_20_facturas_criticas.xlsx")
        else:
            st.success("🎉 Excelente: No se registran comprobantes con saldos vencidos mayores a 75 días.")
