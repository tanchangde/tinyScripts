# 此脚本用于通过文献 DOI 批量查询 Altmetric Score
# 运行该脚本前，请将需要查询的 DOI 参考 sample 文件结构组织
# 待查询文件，请自行重命名并放置在与脚本统一路径下，或修改读入文件路径
# 查询结果保存到当前脚本运行目录下的 “result.csv” 文件，未查询到的将留空。

if(!isTRUE(require("readr"))){install.packages("readr")}
if(!isTRUE(require("stringr"))){install.packages("stringr")}
if(!isTRUE(require("dplyr"))){install.packages("dplyr")}
if(!isTRUE(require("RCurl"))){install.packages("RCurl")}
if(!isTRUE(require("magrittr"))){install.packages("magrittr")}
if(!isTRUE(require("jsonlite"))){install.packages("jsonlite")}
library(readr)
library(stringr)
library(dplyr)
library(magrittr)
library(RCurl)
library(jsonlite)

getAltmetricScore <- function(doi, api = "https://api.altmetric.com/v1/doi/") {
	Sys.sleep(runif(n= 1, min = 0, max = 1))
	httpGET(paste0(api,doi)) %>% 
		parse_json() %>% 
		extract2("score")
}

toWrite <- readr::read_csv("sample.csv") %>% # 如想测试脚本，可以减少 sample 文件查询个数到个位数
	mutate(AltmetricScore = lapply(.[[1]], function(z) try(getAltmetricScore(z)))) %>% 
	mutate(AltmetricScore = str_replace(AltmetricScore,"Error : ",replacement = ""))

write.csv(toWrite,"result.csv",na = "")


