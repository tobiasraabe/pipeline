{% extends 'estimation.r' %}

{% block estimation_method %}
model = glm({{ formula }}, data=df, family=binomial(link="logit"))
{% endblock %}
