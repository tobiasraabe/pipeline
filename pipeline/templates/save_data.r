suppressMessages(library(readr))
library(tools)


save_data <- function(df, path){
    if (file_ext(path) == "feather") {
        write_feather(df, path)
    } else if (file_ext(path) %in% c("csv", "")) {
        write_csv(df, path)
    } else if (file_ext(path) == "rds") {
        saveRDS(df, path)
    } else {
        stop("NotImplementedError")
    }

    return(df)
}
