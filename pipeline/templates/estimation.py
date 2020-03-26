import numpy as np
import joblib
import pandas as pd
import statsmodels.formula.api as smf


{% include 'load_data.py' %}


def fit_model(df):
    {% block estimation_method %}{% endblock %}
    return model


def save_model(model):
    joblib.dump(model, "{{ produces }}")


def main():
    df = load_data("{{ depends_on }}")
    model = fit_model(df)
    save_model(model)


if __name__ == "__main__":
    main()
