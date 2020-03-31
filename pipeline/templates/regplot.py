"""Aligned with https://seaborn.pydata.org/generated/seaborn.regplot.html."""

{% extends 'figure.py' %}

{% block plot %}
    import seaborn as sns

    sns.regplot(
        x="{{ x }}", y="{{ y }}",
        data=df,
        lowess=True,
        scatter=False,
        ax=ax,
    )
{% endblock %}
