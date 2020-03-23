def load_data():
    import pandas as pd

    {% if depends_on.endswith(".feather") %}
    df = pd.read_feather("{{ depends_on }}")
    {% elif depends_on.endswith(".dta") %}
    df = pd.read_stata("{{ depends_on }}")
    {% elif depends_on.endswith(".csv") or not Path(depends_on).suffix %}
    df = pd.read_csv("{{ depends_on }}")
    {% elif depends_on.endswith(".pkl") or depends_on.endswith(".pickle") %}
    df = pd.read_pickle("{{ depends_on }}")
    {% elif depends_on.endswith(".sav") %}
    df = pd.read_spss("{{ depends_on }}")
    {% else %}
    raise NotImplementedError
    {% endif %}

    return df
