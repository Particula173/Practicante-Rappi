import os
import re
import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from analyzer import Analyzer


class Chatbot:

    def __init__(self, analyzer):
        self.analyzer = analyzer

        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.prompt = PromptTemplate(
            input_variables=["contexto", "pregunta"],
            template="""
Eres un analista de datos.

Explica los resultados de forma clara y sencilla.
Además de mostrar los datos, debes interpretarlos.

IMPORTANTE:
- No inventes datos
- Si hay datos, dilo claramente
- Explica qué significan los resultados

CONTEXTO:
{contexto}

PREGUNTA:
{pregunta}

Respuesta:
"""
        )

    # ======================
    # PARSEAR FECHA 🔥
    # ======================
    def parsear_fecha(self, texto):
        meses = {
            "enero": 1, "febrero": 2, "marzo": 3,
            "abril": 4, "mayo": 5, "junio": 6,
            "julio": 7, "agosto": 8, "septiembre": 9,
            "octubre": 10, "noviembre": 11, "diciembre": 12
        }

        texto = texto.lower()

        match = re.search(r'(\d{1,2})\s+de\s+([a-záéíóú]+)(?:\s+del?\s+(\d{4}))?', texto)

        if match:
            dia = int(match.group(1))
            mes = meses.get(match.group(2))
            anio = match.group(3)

            if mes:
                if anio:
                    anio = int(anio)
                else:
                    # usar año del dataset
                    anio = self.analyzer.df['timestamp'].dt.year.mode()[0]

                return pd.Timestamp(year=anio, month=mes, day=dia)

        return None

    # ======================
    # CONTEXTO POR DÍA 🔥
    # ======================
    def construir_contexto(self, analyzer):

        df = analyzer.df

        stats = analyzer.metricas()
        var = analyzer.analisis_variabilidad()
        patrones = analyzer.analisis_patrones()
        caidas = analyzer.analisis_caidas()

        return f"""
Datos del día analizado:

- Registros: {len(df)}
- Desde: {df['timestamp'].min()}
- Hasta: {df['timestamp'].max()}

Métricas principales:
- Promedio: {stats['Promedio']}
- Caídas: {stats['Caídas']}
- Anomalías: {stats['Anomalías']}

Análisis de variabilidad:
- Desviación estándar: {var['std']}
- Rango: {var['rango']}
- Coeficiente de variación: {var['coef_variacion']}
- Nivel de estabilidad: {var['nivel']}

Patrones:
- Hora más inestable: {patrones['hora_mas_inestable']}
- Hora con más caídas: {caidas['hora_mas_critica']}

IMPORTANTE: Hay datos reales para este día.
"""

    # ======================
    # RESPUESTA PRINCIPAL 🔥
    # ======================
    def responder(self, pregunta):

        fecha = self.parsear_fecha(pregunta)

        if fecha is not None:

            analyzer_filtrado = self.analyzer.filtrar_por_fecha(fecha)

            if analyzer_filtrado is None:
                return "No hay datos registrados para esa fecha."

            contexto = self.construir_contexto(analyzer_filtrado)
            pregunta += "\nExplica el comportamiento del sistema ese día."

        else:
            return "Por favor, especifica una fecha (por ejemplo: 5 de febrero)."

        prompt_final = self.prompt.format(
            contexto=contexto,
            pregunta=pregunta
        )

        response = self.llm.invoke(prompt_final)

        return response.content

    # ======================
    # COMPARACIÓN (BONUS)
    # ======================
    def responder_comparacion(self, pregunta, analyzer_a, analyzer_b):

        var_a = analyzer_a.analisis_variabilidad()
        var_b = analyzer_b.analisis_variabilidad()

        contexto = f"""
Comparación de dos días:

Día A:
- Nivel: {var_a['nivel']}
- Desviación estándar: {var_a['std']}

Día B:
- Nivel: {var_b['nivel']}
- Desviación estándar: {var_b['std']}

Explica cuál fue más estable y por qué.
"""

        prompt_final = self.prompt.format(
            contexto=contexto,
            pregunta=pregunta
        )

        response = self.llm.invoke(prompt_final)

        return response.content