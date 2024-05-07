-- See https://github.com/nanotee/nvim-lua-guide for tips

-- define a global function that can be called from our vimrc.vim, allowing us
-- to pass in parameters if needed
_G.mydots_init_plugins = function(scriptvars)
    -- XXX: this didn't seem to work - Octo couldn't find it
    -- vim.cmd("Plug 'ibhagwan/fzf-lua'")
    -- vim.cmd("Plug 'nvim-telescope/telescope.nvim'")
    -- telescope requires plenary
end

-- this thing is handy - should we keep it?
_G.print_lsp_clients = function()
    local clients = vim.lsp.get_active_clients()
    for idx, client in pairs(clients) do
        local filetypes = table.concat(client.config.filetypes or {}, '/')
        print(idx, client.name, filetypes, client.config.cmd_cwd)
    end
end
