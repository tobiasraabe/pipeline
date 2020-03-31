from pathlib import Path
import pandas as pd


def save_data(path):
    path = Path(path)

    if path.suffix == ".feather":
        df = pd.to_feather(path)
    elif path.suffix == ".dta":
        df = pd.to_stata(path)
    elif path.suffix == ".csv" or path.suffix == "":
        df = pd.to_csv(path)
    elif path.suffix in [".pkl", ".pickle"]:
        df = pd.to_pickle(path)
    else:
        raise NotImplementedError

    return df
