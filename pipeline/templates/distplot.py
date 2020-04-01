"""Aligned with https://seaborn.pydata.org/generated/seaborn.distplot.html."""

{% extends 'figure.py' %}

{% block plot %}
    import seaborn as sns

    sns.distplot(
        df["{{ a }}"],
        ax=ax,
    )
{% endblock %}
