{% extends 'estimation.py' %}

{% block estimation_method %}
    model = smf.ols(formula="{{ formula }}", data=df).fit(
        {% if cov_type is defined and cov_type %}cov_type="{{ cov_type }}",{% endif %}
        {% if standard_errors is defined and standard_errors == "robust" %}cov_type="HC1",{% endif %}
    )
{% endblock %}
