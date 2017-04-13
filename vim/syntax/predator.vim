if ! exists('b:syntax')
  let b:syntax = 'predator'
endif

" some reserved words:
" 'beginscope' - signifies that this syntax item gets its own variable scope

syn region pred1Region matchgroup=predDoctype start=!\%1l^predator/1\.0$! end=/\%$/ contains=@clPred1,pred1Comment keepend

syn region pred1Comment contained start=/#/ end=/$/ keepend extend oneline
" a repeat of pred1Comment, but used in between 'many' and the following
" opening parenthesis
syn region pred1RepeatRegionComment contained start=/#/ end=/$/ keepend extend oneline nextgroup=pred1RepeatRegionComment,pred1RepeatRegion skipwhite skipnl
hi! link pred1RepeatRegionComment pred1Comment
" a repeat of pred1Comment, but used in between keywords and the closing
" semicolon.
syn region pred1KeywordComment contained start=/#/ end=/$/ keepend extend oneline nextgroup=pred1KeywordWord,pred1KeywordComment skipwhite skipnl
hi! link pred1KeywordComment pred1Comment
syn cluster clPred1 add=pred1Comment

syn cluster clPred1Patterns add=pred1Regex
syn region pred1Regex matchgroup=pred1RegexDelim start=!/! end=!/! contained keepend extend oneline
      \ contains=@clPred1Regex
syn cluster clPred1Regex add=pred1RegexEscape,pred1RegexSpecial,pred1RegexSpecialSeq,pred1RegexSpecialChar
syn cluster clPred1Regex add=pred1RegexParensRegion,pred1RegexCollectionRegion
syn match pred1RegexEscape /\\./ contained extend
syn match pred1RegexSpecial /[.$^*+?|]/ contained
syn match pred1RegexSpecialChar /\\[srntdw]/ contained
syn match pred1RegexSpecialSeq /\\[b0-9]/ contained
syn region pred1RegexParensRegion matchgroup=pred1RegexParens start=/(\%(?:\)\=/ end=/)/ contained keepend extend
      \ contains=@clPred1Regex
syn region pred1RegexCollectionRegion start=/\[^\=/ end=/]/ contained keepend extend
      \ contains=pred1RegexCollectionRange,pred1RegexSpecialChar

hi! link pred1RegexDelim Statement
hi! link pred1RegexEscape Comment
hi! link pred1RegexSpecial Typedef
hi! link pred1RegexSpecialSeq Typedef
hi! link pred1RegexSpecialChar SpecialChar
hi! link pred1RegexParens Identifier
hi! link pred1RegexCollectionRegion Function

syn cluster clPred1 add=pred1DeclRegion
syn region pred1DeclRegion matchgroup=pred1Decl start=/\h\w\+\_s*:/ end=/;/ keepend extend contained
      \ contains=@clPred1Patterns,pred1Options,pred1KeywordStart,pred1Comment
hi! link pred1Decl Macro

syn keyword pred1Options is_whitespace is_leader contained
hi! link pred1Options Function

syn keyword pred1KeywordStart contained keywords nextgroup=pred1KeywordWord,pred1KeywordComment skipwhite skipnl
hi! link pred1KeywordStart Keyword

syn match pred1Literal /'\%(\\.\|[^\\]\)\{-}'/ contained contains=pred1LiteralEscaped keepend extend
syn match pred1Word /"\w\+"/ contained extend
syn match pred1LiteralEscaped /\\./ contained
syn cluster clPred1Patterns add=pred1Literal,pred1Word

syn cluster clPred1Patterns add=pred1GroupRegion,pred1Choice,pred1Repeat,pred1Alias
syn region pred1GroupRegion matchgroup=pred1Group start=/(/ end=/)/ keepend extend contained
      \ contains=@clPred1Patterns
" a copy of the same, but for used after a repeat
syn region pred1RepeatRegion matchgroup=pred1Repeat start=/(/ end=/)/ keepend extend contained
      \ contains=@clPred1Patterns
hi! link pred1Group Operator
syn keyword pred1Choice or contained
hi! link pred1Choice Operator
syn keyword pred1Repeat maybe many nospace contained nextgroup=pred1RepeatRegion,pred1RepeatRegionComment skipwhite skipnl
hi! link pred1Repeat Number
syn keyword pred1Alias as into contained
hi! link pred1Alias Identifier

syn cluster clPred1 add=pred1ExportRegion
syn region pred1ExportRegion matchgroup=pred1Export start=/\<export\>\%(\_s*:\)\@!/ end=/;/ keepend extend contained
      \ contains=pred1Comment
hi! link pred1Export Keyword

syn sync fromstart

hi! link predDoctype Statement
hi! link pred1Comment Comment
hi! link pred1Literal String
hi! link pred1Word Constant
hi! link pred1WordError Error
hi! link pred1LiteralEscaped SpecialChar
