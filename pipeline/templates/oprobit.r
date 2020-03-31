{% extends 'estimation.r' %}

{% block estimation_method %}
suppressMessages(library(MASS))

# Convert dependent variable to factor which might be lost due to data conversion
# issues.
dependent_variable_label <- trimws(strsplit("{{ formula }}", "~")[[1]][1])
df[[dependent_variable_label]] <- as.factor(df[[dependent_variable_label]])

model <- polr({{ formula }}, data=df, method="probit", Hess=TRUE)
{% endblock %}
