syn match gitSummarySpecial contained /\(====*\)[^=].\{-\}\1/ containedin=gitRebaseSummary
hi! link gitSummarySpecial Operator

