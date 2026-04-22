import pandas as pd

class DataProcessor:

    def __init__(self, files):
        self.files = files

    def procesar_archivo(self, path):
        data = pd.read_csv(path)

        df_time = data.drop(columns=[
            'Plot name', 'metric (sf_metric)', 'Value Prefix', 'Value Suffix'
        ])

        df_time = df_time.dropna(how='all')
        row = df_time.iloc[0]

        df_long = row.reset_index()
        df_long.columns = ['timestamp', 'availability']

        df_long['timestamp'] = (
            df_long['timestamp']
            .astype(str)
            .str.replace(r' GMT.*', '', regex=True)
        )

        df_long['availability'] = (
            df_long['availability']
            .astype(str)
            .str.replace(',', '')
        )

        df_long['timestamp'] = pd.to_datetime(df_long['timestamp'], errors='coerce')
        df_long['availability'] = pd.to_numeric(df_long['availability'], errors='coerce')

        return df_long.dropna().sort_values('timestamp')

    def cargar(self):
        dfs = []
        for f in self.files:
            df_temp = self.procesar_archivo(f)
            df_temp['source'] = f
            dfs.append(df_temp)

        return pd.concat(dfs).sort_values('timestamp')