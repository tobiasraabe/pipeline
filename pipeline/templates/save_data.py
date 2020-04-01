from pathlib import Path


def save_data(df, path):
    path = Path(path)

    if path.suffix == ".feather":
        df.to_feather(path)
    elif path.suffix == ".dta":
        df.to_stata(path)
    elif path.suffix == ".csv" or path.suffix == "":
        df.to_csv(path)
    elif path.suffix in [".pkl", ".pickle"]:
        df.to_pickle(path)
    else:
        raise NotImplementedError

    return df
