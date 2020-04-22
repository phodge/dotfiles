aug AutoChmod
au!
aug end

com! -bar AutoChmodEnable  au! AutoChmod BufWritePost * call AutoChmod#PostWrite()
com! -bar AutoChmodDisable au! AutoChmod
com! -bar AutoChmodToggleVerbose call AutoChmod#ToggleVerbose()

AutoChmodEnable
