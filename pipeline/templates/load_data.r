suppressMessages(library(tidyverse))


load_data <- function(){
    {% if depends_on.endswith(".feather") %}
    df <- read_feather("{{ depends_on }}")
    {% elif depends_on.endswith(".csv") or not Path(depends_on).suffix %}
    df <- read_csv("{{ depends_on }}")
    {% else %}
    stop("NotImplementedError")
    {% endif %}

    return(df)
}
