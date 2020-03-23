{% extends 'estimation.r' %}

{% block estimation_method %}
model = lm({{ formula }}, data=df)
{% endblock %}
