{% extends 'estimation.py' %}

{% block estimation_method %}
    model = smf.logit(formula="{{ formula }}", data=df).fit()
{% endblock %}
