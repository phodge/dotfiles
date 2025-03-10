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

function _get_ts_ls_config(with_vue)
    config = {
        init_options = {
            plugins = {},
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
            vim.o.formatexpr = ""
            vim.o.tagfunc = ""
        end,
    }
    if with_vue then
        config.filetypes = {"javascript", "typescript", "vue"}
    else
        config.filetypes = {"javascript", "typescript"}
    end

    if with_vue then
        table.insert(config.init_options.plugins, {
            name = "@vue/typescript-plugin",
            location = vim.g.pete_dotfiles_root .. "/nvim_ts/node_modules/@vue/language-server",
            languages = {"vue", "javascript", "typescript"},
        })
    end

    return config
end

function _get_default_pylsp_settings()
    return {
        pylsp = {
            -- See https://github.com/python-lsp/python-lsp-server/blob/develop/CONFIGURATION.md
            plugins = {
                -- disable most plugins
                pycodestyle = { enabled = false },
                pylint = { enabled = false },
                pyflakes = { enabled = false },
                autopep8 = { enabled = false },
                flake8 = { enabled = false },
                -- jedi_completion = { enabled = false, },
                jedi_definition = { enabled = true, },
                jedi_hover = { enabled = true, },
                jedi_references = { enabled = true, },
                -- jedi_signature_help = { enabled = false, },
                mccabe = { enabled = false, },
                -- requires python-lsp-isort installed in the virtualenv
                isort = {
                    -- https://github.com/chantera/python-lsp-isort?tab=readme-ov-file#configuration
                    enabled = false,
                },
                -- requires python-lsp-black installed in the virtualenv
                black = {
                    -- reference: https://github.com/python-lsp/python-lsp-black?tab=readme-ov-file#configuration
                    enabled = false,
                },
                -- requires python-lsp-ruff installed in the virtualenv
                ruff = {
                    enabled = false,
                    -- XXX: I *think* this enables the isort rules for ruff but I'm really not sure
                    extendSelect = { "I" },
                },
                -- requires pylsp-mypy installed in the virtualenv
                pylsp_mypy = {
                    enabled = false,
                    dmypy = false,
                    -- don't run on every keystroke
                    live_mode = false,
                    -- try to let neovim know when mypy is running
                    report_progress = true,
                    -- XXX: don't touch this, I haven't been able to work out what it does
                    -- overrides = { },
                },
            },
        },
    }
end

-- TODO(DOTFILES049): can we have pylsp installed somewhere global so that we don't have to install it in all our virtualenvs?
function _get_pylsp_config(signatures)
    return {
        settings = _get_default_pylsp_settings(),
        on_attach = function(client, bufnr)
            -- TODO: is there a way to use workspace/configuration request to get the current configuration before updating?
            -- See https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/
            local settings = _get_default_pylsp_settings()

            if signatures then
                settings.pylsp.plugins.jedi_signature_help.enabled = true
                client.notify('workspace/didChangeConfiguration', { settings = settings })
            end

            -- XXX: steal this back from PyLSP - it's not capable of doing
            -- partial formatting and we want to let our regular formatting
            -- settings from our ftplugin do the work
            -- TODO(DOTFILES043) should be able to use this for ts_ls also
            vim.o.formatexpr = ""

            -- XXX: also clear this so that PyLSP doesn't try doing "tags"
            -- stuff for us - Gutentags does a fine job of this for us already.
            -- TODO(DOTFILES043) should be able to use this for ts_ls also
            vim.o.tagfunc = ""
        end,
    }
end

function _has_client(findname)
    local clients = vim.lsp.get_clients({bufnr = vim.fn.bufnr()})
    for _, client in ipairs(clients) do
        if client.name == findname then
            return true
        end
    end
    return false
end

exports.init_ts_ls = function(opts)
    if not _has_client('ts_ls') then
        -- XXX: If you look at the lspconfig package's ts_ls.lua you'll see
        -- that it's doing very (very!) little and we might be better off
        -- managing the server lifecycle ourself to get the desired per-buffer
        -- behaviour. This might make it possible to get rid of our
        -- _has_client() hack as well
        require("lspconfig").ts_ls.setup(_get_ts_ls_config(opts.vue))
    end
end

exports.init_null_ls = function(want_eslint_d)
    if not _has_client('null-ls') then
        local null_ls = require('null-ls')

        -- TODO: discover more things we can do with null-ls:
        -- https://github.com/jose-elias-alvarez/null-ls.nvim
        local sources = {
            null_ls.builtins.formatting.prettier,
        }

        if want_eslint_d then
            -- We use eslint_d for linting - apparently it is much faster, although
            -- in my testing both eslint and eslint_d took 18-25 seconds to
            -- execute, possibly due to the typescript checking
            table.insert(sources, null_ls.builtins.diagnostics.eslint_d)
            -- TODO(DOTFILES054) turn this back on?
            -- table.insert(sources, null_ls.builtins.code_actions.eslint_d)
        end

        null_ls.setup({
            sources = sources,
            on_attach = function(client, bufnr)
                -- XXX: try to prevent these being defined for typescript files
                vim.o.formatexpr = ""
                vim.o.tagfunc = ""
            end,
        })
    end
end

exports.init_pylsp = function()
    if not _has_client('pylsp') then
        -- TODO: do these need to be turned on for these to work?
        -- (sticky notes)
        require("lspconfig").pylsp.setup(_get_pylsp_config(false))
    end
end

return exports
