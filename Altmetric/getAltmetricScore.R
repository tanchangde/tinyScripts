# 此脚本用于通过文献 DOI 批量查询 Altmetric Score
# 运行该脚本前，请将需要查询的 DOI 置换 toQuery.csv 文件中的 DOI 条目
# toQuery.csv 文件在请放置到当前 R 会话到工作目录下
# 当前 R 会话工作目录可通过在控制台运行 getwd() 函数明确
# 若控制台提示查询超时（Timed out 字样），大概率是当前 IP 被识别频繁查询
# 请利用三方工具切换全局 IP 再次运行脚本查询，直至提示“🎉恭喜，你已完成所有条目查询！”
# 本脚本支持中断后与新增 DOI 增量查询
# 即无需因中断重查之前查询过的结果，如确有需要重新查询，请删除 queryResult 文件夹 再次运行该脚本
# 运行脚本前，请确保已保存并关闭 toQuery.csv
# 查询结果将合并保存到当前脚本运行工作目录下的 queryResult.csv 文件，未查询到的将留空
 
# 加载必要 package

pkgsToLoad = c("readr", "stringr", "dplyr", "purrr", "RCurl", "magrittr", "jsonlite", "fs")
pkgsToInstall <- pkgsToLoad[!pkgsToLoad %in% installed.packages()]

if( length(pkgsToInstall) > 0){
	for(lib in pkgsToInstall) install.packages(lib)
}

sapply(pkgsToLoad, require, character.only=TRUE)

# 构造接口查询函数

getAltmetricScore <- function(doi, api = "https://api.altmetric.com/v1/doi/") {
	sleepTime <-  runif(n= 1, min = 0, max = 1)
	cat("\n[🐶友好调用] 划水 ", round(sleepTime, digits = 2), " 秒")
	Sys.sleep(sleepTime)
	cat("\n[🔍开始查询]", doi, "的 Altmetric Score...")
	tryCatch({
	score <- httpGET(paste0(api,doi)) %>% 
			parse_json() %>% 
			extract2("score")
	cat("\n[🍒查询结果] ")
	cat(format(score), fill = getOption("width"))
	invisible(score)
	},error = function(e) {
		cat("\n[🍒查询结果] ")
		cat("未匹配到\n")
		invisible("")
	}
	)
}

# 创建查询结果文件夹

pathToResult <- paste0(getwd(),"/queryResult")
cat("查询结果将保存至", pathToResult)

if (!"queryResult" %in% dir_ls()) {
	dir_create(path = "queryResult")
	toQuery <- readr::read_csv("toQuery.csv", show_col_types = FALSE) %>% 
		extract2(1)
} else if(length(dir_ls(pathToResult)) == 0){
	toQuery <- readr::read_csv("toQuery.csv", show_col_types = FALSE) %>% 
		extract2(1)
} else {
	historyQuery <- dir_ls(pathToResult) %>%  # 遍历结果文件夹文件并合并
		map_dfr(read_csv, show_col_types = FALSE) %>% 
		distinct()
	toQuery <- readr::read_csv("toQuery.csv", show_col_types = FALSE) %>% 
		left_join(historyQuery, by = c("DOI" = "doiNum")) %>% 
		filter(is.na(isQuery)) %>% # 剔除已查询条目
		extract2(1)
}

if (length(toQuery) > 0){
	for (doiNum in toQuery) {
		tmpResult <-  getAltmetricScore(doi = doiNum)
		tmpTable <- tibble(doiNum, tmpResult, isQuery = 1)
		tmpFileName <- paste0((str_extract_all(string = doiNum, pattern = "\\w")) [[1]],collapse = "")
		write.csv(tmpTable,file = paste0(pathToResult,"/", tmpFileName,".csv"), row.names = FALSE, na = "")
		cat("\n查询结果已保存。\n")
	}
	updateQuery <- dir_ls(pathToResult) %>%  # 遍历结果文件夹文件并合并
		map_dfr(read_csv, show_col_types = FALSE) %>% 
		distinct() %>% 
		rename(DOI = doiNum,AltmetricScore = tmpResult) %>% 
		select(DOI, AltmetricScore)
	write.csv(updateQuery, file = paste0(getwd(),"/","queryResult.csv"), row.names = FALSE, na = "")
	} else {
		cat("\n🎉恭喜，你已完成所有条目查询！")
		}