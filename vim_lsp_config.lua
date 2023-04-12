-- See https://github.com/nanotee/nvim-lua-guide for tips

require("lspconfig").tsserver.setup({
    on_attach = function(client, bufnr)
        client.server_capabilities.documentFormattingProvider = false
        client.server_capabilities.documentRangeFormattingProvider = false
        local ts_utils = require("nvim-lsp-ts-utils")
        ts_utils.setup({})
        ts_utils.setup_client(client)
    end,
})

local null_ls = require('null-ls')
null_ls.setup({
    -- TODO: discover more things we can do with null-ls:
    -- https://github.com/jose-elias-alvarez/null-ls.nvim
    sources = {
        -- We use eslint_d for linting - apparently it is much faster, although
        -- in my testing both eslint and eslint_d took 18-25 seconds to
        -- execute, possibly due to the typescript checking
        null_ls.builtins.diagnostics.eslint_d,
        null_ls.builtins.code_actions.eslint_d,
        null_ls.builtins.formatting.prettier,
    },
})
