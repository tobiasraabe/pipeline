suppressMessages(library(readr))
library(tools)


load_data <- function(path){
    if (file_ext(path) == "feather") {
        write_feather(df, path)
    } else if (file_ext(path) %in% c("csv", "")) {
        write_csv(df, path)
    } else {
        stop("NotImplementedError")
    }

    return(df)
}
