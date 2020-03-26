{% extends 'estimation.py' %}

{% block estimation_method %}
    model = smf.ols(formula="{{ formula }}", data=df).fit()
{% endblock %}
