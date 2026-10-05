import pandas as pd






def load_dataset():
    ocupados_df = pd.read_csv("../dataset/CSV/Ocupados.CSV")
    noocupados_df = pd.read_csv("../dataset/CSV/No ocupados.CSV")
