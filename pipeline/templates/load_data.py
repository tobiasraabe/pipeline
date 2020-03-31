from pathlib import Path
import pandas as pd


def load_data(path):
    path = Path(path)
    if path.suffix == ".feather":
        df = pd.read_feather(path)
    elif path.suffix == ".dta":
        df = pd.read_stata(path)
    elif path.suffix == ".csv" or path.suffix == "":
        df = pd.read_csv(path)
    elif path.suffix in [".pkl", ".pickle"]:
        df = pd.read_pickle(path)
    elif path.suffix == ".sav":
        df = pd.read_spss(path)
    else:
        raise NotImplementedError

    return df
