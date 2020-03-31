{% extends 'estimation.r' %}

{% block estimation_method %}
suppressMessages(library(MASS))

model <- polr({{ formula }}, data=df, method="probit", Hess=TRUE)
{% endblock %}
