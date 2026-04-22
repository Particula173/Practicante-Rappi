import os
from data_processor import DataProcessor
from analyzer import Analyzer
from dashboard import DashboardApp

DATA_FOLDER = "data"

# Cargar automáticamente todos los CSV
FILES = [
    os.path.join(DATA_FOLDER, f)
    for f in os.listdir(DATA_FOLDER)
    if f.endswith(".csv")
]

# Procesamiento
processor = DataProcessor(FILES)
df = processor.cargar()

# Análisis
analyzer = Analyzer(df)

# App
app = DashboardApp(analyzer)
app.run()