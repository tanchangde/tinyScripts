# 说明 ----

# 通过文献 DOI 批量查询 Altmetric Score
#
# 运行该脚本前，你应当了解 R 语言基础及其脚本执行，若有困难请搜索或求助大语言模型
#
# 请将待查询的 DOI 完全替换 toQuery.csv 文件中的 DOI 条目
# toQuery.csv 文件在请放置到当前 R 会话工作目录下
#
# 若控制台提示查询超时（"...Timed out" 字样），有可能是当前 IP 被识别频繁查询
# 请利用三方工具切换全局 IP 再次运行脚本查询，直至提示“🎉恭喜，你已完成所有条目
# 查询！”
#
# 此脚本支持中断续查与增量 DOI 查询
# 如确有需要重新查询，请删除 queryResult 文件夹或需要重查结果文件，再次运行该脚本
# 运行脚本前，请确保已保存并关闭 toQuery.csv
#
# 查询完毕后，结果将合并保存到当前脚本运行工作目录下的 queryResult.csv 文件，未
# 查询到的将留空
# 加载必要 package

pkgsToLoad <- c("readr", "stringr", "dplyr", "purrr", "RCurl", "magrittr", "jsonlite", "fs")
pkgsToInstall <- pkgsToLoad[!pkgsToLoad %in% installed.packages()]

if(length(pkgsToInstall) > 0){
	for(lib in pkgsToInstall) install.packages(lib)
}

sapply(pkgsToLoad, require, character.only = TRUE)

# 构造接口查询函数

getAltmetricScore <- function(doi, api = "https://api.altmetric.com/v1/doi/") {
	sleepTime <- runif(n = 1, min = 0, max = 1)
	cat("\n[🐶友好调用] 划水", round(sleepTime, digits = 2), "秒")
	Sys.sleep(sleepTime)
	cat("\n[🔍开始查询]", doi, "的 Altmetric Score...")
	tryCatch({
		score <- httpGET(paste0(api, doi)) %>% 
			parse_json() %>% 
			extract2("score")
		cat("\n[🍒查询结果] ")
		cat(format(score), fill = getOption("width"))
		invisible(score)
	}, error = function(e) {
		cat("\n[🍒查询结果] ")
		cat(e$message, "\n")
		invisible(e$message)
	}
	)
}

# 创建查询结果文件夹&读取需查询条目

pathToResult <- paste0(getwd(), "/queryResult")
cat("查询结果将保存至", pathToResult)

if (!"queryResult" %in% dir_ls()) {
	dir_create(path = "queryResult")
	toQuery <- read_csv("toQuery.csv", show_col_types = FALSE) %>% 
		extract2(1)
} else if(length(dir_ls(pathToResult)) == 0){
	toQuery <- read_csv("toQuery.csv", show_col_types = FALSE) %>% 
		extract2(1)
} else {
	historyQuery <- dir_ls(pathToResult) %>%  # 遍历结果文件夹文件并合并
		map_dfr(read_csv, show_col_types = FALSE, col_types = cols(.default = "c")) %>% 
		distinct()
	toQuery <- read_csv("toQuery.csv", show_col_types = FALSE) %>% 
		left_join(historyQuery, by = c("DOI" = "doiNum")) %>% 
		filter(is.na(isQuery) | tmpResult == "Failed to connect to api.altmetric.com port 443: Operation timed out") %>% # 剔除已查询条目&增补查询超时条目
		extract2(1)
}

# 查询&合并结果并保存

if (length(toQuery) > 0){
	for (doiNum in toQuery) {
		tmpResult <-  getAltmetricScore(doi = doiNum)
		tmpTable <- tibble(doiNum, tmpResult, isQuery = 1)
		tmpFileName <- paste0((str_extract_all(string = doiNum, pattern = "\\w"))[[1]], collapse = "")
		write.csv(tmpTable, file = paste0(pathToResult, "/", tmpFileName, ".csv"), row.names = FALSE, na = "")
		cat("\n查询结果已保存。\n")
	}
} else {
	updateQuery <- dir_ls(pathToResult) %>%  # 遍历结果文件夹文件并合并
		map_dfr(read_csv, show_col_types = FALSE, col_types = cols(.default = "c")) %>% 
		distinct() %>% 
		rename(DOI = doiNum, AltmetricScore = tmpResult) %>% 
		select(DOI, AltmetricScore)
	write.csv(updateQuery, file = paste0(getwd(), "/", "queryResult.csv"), row.names = FALSE, na = "")
	cat("\n🎉恭喜，你已完成所有条目查询！")
}