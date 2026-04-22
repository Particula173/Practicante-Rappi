import numpy as np
import pandas as pd

class Analyzer:

    def __init__(self, df):
        self.df = df.copy()
        self.procesar()

    def procesar(self):
        df = self.df

        df['delta'] = df['availability'].diff()
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day_name()

        # ======================
        # ANOMALÍAS
        # ======================
        mean = df['availability'].mean()
        std = df['availability'].std()

        df['anomaly'] = (
            (df['availability'] < mean - 2*std) |
            (df['availability'] > mean + 2*std)
        )

        # ======================
        # CAÍDAS
        # ======================
        threshold = df['delta'].quantile(0.05)
        self.df_drops = df[df['delta'] < threshold]

        # ======================
        # HEALTH
        # ======================
        df['health_score'] = df['availability'] / df['availability'].max()

    # ======================
    # FILTRO POR FECHA 🔥
    # ======================
    def filtrar_por_fecha(self, fecha):
        inicio = fecha.normalize()
        fin = inicio + pd.Timedelta(days=1)

        df_filtrado = self.df[
            (self.df['timestamp'] >= inicio) &
            (self.df['timestamp'] < fin)
        ]

        if df_filtrado.empty:
            return None

        return Analyzer(df_filtrado)

    # ======================
    # ESTADÍSTICAS
    # ======================
    def estadisticas(self):
        df = self.df

        return {
            "Media": df['availability'].mean(),
            "Mediana": df['availability'].median(),
            "Desviación estándar": df['availability'].std(),
            "Varianza": df['availability'].var(),
            "Q1": df['availability'].quantile(0.25),
            "Q3": df['availability'].quantile(0.75)
        }

    # ======================
    # MÉTRICAS SIMPLES
    # ======================
    def metricas(self):
        return {
            "Promedio": round(self.df['availability'].mean(), 2),
            "Min": int(self.df['availability'].min()),
            "Max": int(self.df['availability'].max()),
            "Caídas": len(self.df_drops),
            "Anomalías": int(self.df['anomaly'].sum())
        }

    # ======================
    # CAÍDAS
    # ======================
    def analisis_caidas(self):
        df = self.df_drops.copy()

        if df.empty:
            return {
                "total_caidas": 0,
                "hora_mas_critica": None,
                "dia_mas_critico": None
            }

        hora = df['timestamp'].dt.hour.value_counts().idxmax()
        dia = df['timestamp'].dt.day_name().value_counts().idxmax()

        return {
            "total_caidas": len(df),
            "hora_mas_critica": int(hora),
            "dia_mas_critico": dia
        }

    # ======================
    # PATRONES
    # ======================
    def analisis_patrones(self):
        df = self.df

        var_por_hora = df.groupby('hour')['availability'].std()
        hora_inestable = var_por_hora.idxmax()

        return {
            "hora_mas_inestable": int(hora_inestable)
        }

    # ======================
    # VARIABILIDAD POR HORA
    # ======================
    def variabilidad_por_hora(self):
        return self.df.groupby('hour')['availability'].std().fillna(0)

    # ======================
    # VARIABILIDAD GLOBAL 🔥 NUEVO
    # ======================
    def analisis_variabilidad(self):
        df = self.df

        std = df['availability'].std()
        rango = df['availability'].max() - df['availability'].min()
        media = df['availability'].mean()

        cv = std / media if media != 0 else 0

        if cv < 0.05:
            nivel = "muy estable"
        elif cv < 0.1:
            nivel = "estable"
        elif cv < 0.2:
            nivel = "inestable"
        else:
            nivel = "muy inestable"

        return {
            "std": round(std, 2),
            "rango": round(rango, 2),
            "coef_variacion": round(cv, 3),
            "nivel": nivel
        }

    # ======================
    # TENDENCIA
    # ======================
    def tendencia(self):
        df = self.df

        inicio = df['availability'].iloc[0]
        fin = df['availability'].iloc[-1]

        if fin > inicio:
            return "creciente"
        elif fin < inicio:
            return "decreciente"
        else:
            return "estable"