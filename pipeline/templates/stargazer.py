import joblib

from stargazer.stargazer import Stargazer


def load_model(path):
    model = joblib.load(path)

    return model


def create_table(models):
    stargazer = Stargazer(models)

    {% if produces.endswith(".tex") %}
    table = stargazer.render_latex()
    {% elif produces.endswith(".html") or not Path(produces).suffix %}
    table = stargazer.render_html()
    {% else %}
    raise NotImplementedError
    {% endif %}

    with open("{{ produces }}", "w") as file:
        file.write(table)


def main():
    models = []
    for path in {{ ensure_list(depends_on) }}:
        model = load_model(path)
        models.append(model)

    create_table(models)

{% include 'ifmain.py' %}
