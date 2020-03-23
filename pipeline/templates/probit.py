{% extends 'estimation.py' %}

{% block estimation_method %}
    model = smf.probit(formula="{{ formula }}", data=df).fit()
{% endblock %}
