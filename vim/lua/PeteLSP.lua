-- XXX: I spent a great deal of time ending up at this layout for per-project /
-- per-buffer LSP config and learned the following along the way:
--
--   1. If you use `lspconfig.setup({filetypes={/*nothing*/}}` then it will
--      either target all filetypes or else use the default types for the
--      language server, and the server will start without asking.
--   2. If you use `lspconfig.setup({filetypes={"__match_nothing__"}})` then it
--      won't start up automatically but also won't be available in
--      vim.lsp.get_clients() meaning that you can't find a client_id for it
--      and start it manually.
--   3. `:LspStart <config_name>` doesn't limit itself to lspconfig servers
--      with that name, it'll start up all of them that match by filetype.
--   4. If you're calling `lspconfig.xxx.setup()` after the end of your
--      .vimrc/init.vim then you'll also have to call `:LspStart` afterwards to
--      boot up the newly defined server.
--   5. Using `lspconfig.setup {autostart = false }` did prevent the server
--      from starting up, but it would also be absent from
--      vim.lsp.get_clients() so you again you couldn't start it up manually
--      later.
--
--
-- With the above in mind, the following layout allows me to put the following
-- in my vim-project-config to "mostly" load servers on-demand:
--
--   if &filetype == 'something'
--     let b:ale_enabled = 0
--     lua require('PeteLSP').init_ts_ls({some_opt = true})
--     lua require('PeteLSP').init_null_ls()
--     LspStart
--   endif


exports = {}

function _get_ts_ls_config()
    config = {
        init_options = {
            preferences = {
                -- this is for fudgemoney
                -- TODO: DOTFILES002: how to configure this per-project?
                importModuleSpecifierPreference = 'relative',
            },
        },
        on_attach = function(client, bufnr)
            client.server_capabilities.documentFormattingProvider = false
            client.server_capabilities.documentRangeFormattingProvider = false
            local ts_utils = require("nvim-lsp-ts-utils")
            ts_utils.setup({})
            ts_utils.setup_client(client)

        -- TODO: DOTFILES002: set per-buffer or per-project config settings here
        end,
    }
    return config
end

exports.init_ts_ls = function(opts)
    require("lspconfig").ts_ls.setup(_get_ts_ls_config(opts.vue))
end

exports.init_null_ls = function()
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
end

return exports