suppressMessages(library(readr))
library(tools)
library(feather)


load_data <- function(path){
    if (file_ext(path) == "feather") {
        df <- read_feather(path)
    } else if (file_ext(path) %in% c("csv", "")) {
        df <- read_csv(path)
    } else if (file_ext(path) == "rds") {
        df <- readRDS(path)
    } else {
        stop("NotImplementedError")
    }

    return(df)
}
