# https://www.jakeruss.com/cheatsheets/stargazer/
# https://www.rdocumentation.org/packages/stargazer/versions/5.2.2/topics/stargazer

suppressMessages(library(stargazer))

load_model <- function(path){
    model <- readRDS(path)
}

models <- sapply(c{{ tuple(ensure_list(depends_on)) }}, load_model)

capture.output(stargazer(models, title="Regression Results", align=TRUE, out="{{ produces }}"))
