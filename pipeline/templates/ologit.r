{% extends 'estimation.r' %}


{% block estimation_method %}
suppressMessages(library(MASS))

model <- polr({{ formula }}, data=df, method="logistic", Hess=TRUE)
{% endblock %}
