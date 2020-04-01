# https://www.jakeruss.com/cheatsheets/stargazer/
# https://www.rdocumentation.org/packages/stargazer/versions/5.2.2/topics/stargazer

suppressMessages(library(stargazer))
library(xtable)
library(functional)


load_model <- function(path){
    model <- readRDS(path)
    return(model)
}


format_covariate_labels <- function(model){
    labels <- sanitize(rownames(coef(summary(model))), type="latex")
    return(labels)
}


format_dependent_labels <- function(model){
    label <- sanitize(all.vars(formula(model))[1], type="latex")
    return(label)
}


models <- lapply({{ ensure_r_vector(depends_on) }}, load_model)

curry <- Curry(
    stargazer,
    title="Regression Results",
    align=TRUE,
    covariate.labels = sapply(models, format_covariate_labels),
    dep.var.labels = sapply(models, format_dependent_labels),
    out="{{ produces }}"
)

capture.output(do.call(curry, models))
