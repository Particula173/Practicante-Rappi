import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from analyzer import Analyzer
from chatbot import Chatbot

class DashboardApp:

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def _apply_time_filter(self, df):
        """Apply time filter based on user selection."""
        modo = st.sidebar.radio(
            "Modo de selección de tiempo",
            ["Rango manual", "Periodo rápido"]
        )

        if modo == "Rango manual":
            fecha_inicio = st.sidebar.date_input(
                "Fecha inicio",
                value=df['timestamp'].min().date()
            )
            hora_inicio = st.sidebar.time_input(
                "Hora inicio",
                value=df['timestamp'].min().time()
            )
            fecha_fin = st.sidebar.date_input(
                "Fecha fin",
                value=df['timestamp'].max().date()
            )
            hora_fin = st.sidebar.time_input(
                "Hora fin",
                value=df['timestamp'].max().time()
            )

            inicio = pd.to_datetime(f"{fecha_inicio} {hora_inicio}")
            fin = pd.to_datetime(f"{fecha_fin} {hora_fin}")

            if inicio >= fin:
                st.sidebar.error("La fecha inicial debe ser menor que la final")
                return df

            df = df[(df['timestamp'] >= inicio) & (df['timestamp'] <= fin)]

        else:
            opcion = st.sidebar.selectbox(
                "Periodo",
                ["Último día", "Últimos 2 días", "Últimos 3 días", "Todo"]
            )
            max_time = df['timestamp'].max()

            if opcion == "Último día":
                df = df[df['timestamp'] >= max_time - pd.Timedelta(days=1)]
            elif opcion == "Últimos 2 días":
                df = df[df['timestamp'] >= max_time - pd.Timedelta(days=2)]
            elif opcion == "Últimos 3 días":
                df = df[df['timestamp'] >= max_time - pd.Timedelta(days=3)]

        return df

    def _show_normal_analysis(self, df_original):
        """Display normal analysis mode."""
        df = df_original.copy()
        st.sidebar.header("Filtros")
        df = self._apply_time_filter(df)

        # 🔥 FIX: evitar errores si no hay datos
        if df.empty:
            st.warning("No hay datos en el rango seleccionado")
            return

        analyzer = Analyzer(df)

        st.subheader("Indicadores clave")
        m = analyzer.metricas()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Promedio", m["Promedio"])
        col2.metric("Min", m["Min"])
        col3.metric("Max", m["Max"])
        col4.metric("Caídas", m["Caídas"])

        st.caption(f"Analizando datos desde {df['timestamp'].min()} hasta {df['timestamp'].max()}")

        # 🔥 FIX typo
        st.subheader("Evolución del sistema")

        fig, ax = plt.subplots(figsize=(14,5))
        ax.plot(df['timestamp'], df['availability'])
        ax.set_title("Disponibilidad en el tiempo")
        ax.grid(alpha=0.3)
        st.pyplot(fig)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribución")
            fig2, ax2 = plt.subplots()
            ax2.hist(df['availability'], bins=30)
            st.pyplot(fig2)

        with col2:
            st.subheader("Boxplot")
            fig3, ax3 = plt.subplots()
            ax3.boxplot(df['availability'], vert=False)
            st.pyplot(fig3)

        st.subheader("Variabilidad por hora")
        var_h = analyzer.variabilidad_por_hora()
        st.bar_chart(var_h)

        st.subheader("Detección de caídas")
        fig4, ax4 = plt.subplots(figsize=(14,5))
        ax4.plot(df['timestamp'], df['availability'], alpha=0.3)
        drops = df[df['availability'].diff() < df['availability'].diff().quantile(0.05)]
        ax4.scatter(drops['timestamp'], drops['availability'], color='red')
        st.pyplot(fig4)

        patrones = analyzer.analisis_patrones()
        hora = patrones['hora_mas_inestable']
        st.info(f"La mayor inestabilidad ocurre alrededor de la hora {hora}")

        st.subheader("Asistente Inteligente")
        chatbot = Chatbot(analyzer)
        q = st.text_input("Haz una pregunta sobre el sistema:")
        if q:
            try:
                st.success(chatbot.responder(q))
            except Exception as e:
                st.error(f"Error en el chatbot: {e}")

    def _show_comparison_analysis(self, df_original):
        """Display comparison analysis mode."""
        st.sidebar.header("Comparación de rangos")

        inicio_a = st.sidebar.date_input("Inicio A", df_original['timestamp'].min().date())
        fin_a = st.sidebar.date_input("Fin A", df_original['timestamp'].max().date())
        inicio_b = st.sidebar.date_input("Inicio B", df_original['timestamp'].min().date(), key="b1")
        fin_b = st.sidebar.date_input("Fin B", df_original['timestamp'].max().date(), key="b2")

        # 🔥 FIX: usar datetime real
        df_a = df_original[
            (df_original['timestamp'] >= pd.to_datetime(inicio_a)) &
            (df_original['timestamp'] <= pd.to_datetime(fin_a))
        ]

        df_b = df_original[
            (df_original['timestamp'] >= pd.to_datetime(inicio_b)) &
            (df_original['timestamp'] <= pd.to_datetime(fin_b))
        ]

        # 🔥 FIX: evitar vacío
        if df_a.empty or df_b.empty:
            st.warning("Uno de los rangos no tiene datos")
            return

        analyzer_a = Analyzer(df_a)
        analyzer_b = Analyzer(df_b)

        st.subheader("Comparación de métricas")
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Rango A")
            st.write(analyzer_a.metricas())
        with col2:
            st.write("### Rango B")
            st.write(analyzer_b.metricas())

        st.subheader("Comparación temporal")
        fig, ax = plt.subplots()
        ax.plot(df_a['timestamp'], df_a['availability'], label="Rango A")
        ax.plot(df_b['timestamp'], df_b['availability'], label="Rango B")
        ax.legend()
        st.pyplot(fig)

        if analyzer_a.metricas()['Promedio'] > analyzer_b.metricas()['Promedio']:
            st.success("Rango A tiene mejor desempeño")
        else:
            st.warning("Rango B tiene mejor desempeño")

        st.subheader("Chatbot comparativo")
        chatbot = Chatbot(analyzer_a)
        q = st.text_input("Pregunta sobre la comparación")
        if q:
            try:
                respuesta = chatbot.responder_comparacion(q, analyzer_a, analyzer_b)
                st.success(respuesta)
            except Exception as e:
                st.error(f"Error en el chatbot: {e}")

    def run(self):

        st.set_page_config(layout="wide")
        st.title("Dashboard Inteligente de Disponibilidad")

        df_original = self.analyzer.df.copy()

        modo_analisis = st.sidebar.radio(
            "Modo de análisis",
            ["Análisis normal", "Comparación de rangos"]
        )

        if modo_analisis == "Análisis normal":
            self._show_normal_analysis(df_original)
        else:
            self._show_comparison_analysis(df_original)