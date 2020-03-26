suppressMessages(library(tidyverse))

{% include 'load_data.r' %}

df = suppressMessages(load_data("{{ depends_on }}"))

df %>% mutate_if(is.character, as.factor) -> df

{% block estimation_method %}{% endblock %}

saveRDS(model, "{{ produces }}")
