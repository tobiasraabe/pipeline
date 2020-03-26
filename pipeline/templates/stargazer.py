import joblib
from pathlib import Path
from stargazer.stargazer import Stargazer


def load_model(path):
    model = joblib.load(path)
    return model


def create_table(models, path):
    path = Path(path)
    stargazer = Stargazer(models)

    if path.suffix == ".tex":
        table = stargazer.render_latex()
    elif path.suffix == ".html":
        table = stargazer.render_html()
    else:
        raise NotImplementedError

    with open(path, "w") as file:
        file.write(table)


def main():
    models = [load_model(path) for path in {{ ensure_list(depends_on) }}]
    create_table(models, "{{ produces }}")


if __name__ == "__main__":
    main()
