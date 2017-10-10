

- RunTestsByConfig(file_or_dir, config)
  - if there is a buffer open for file_or_dir, set a b:var in it so that neovim knows we're running its tests
  - if there is a g:spacetea_display var set, use that for display; otherwise
    call GetAutoDisplay() to know where to show test results

- GetConfigPath(file_or_dir)
  - find project top level relative to file_or_dir and return PROJECT_PATH/.spacetea

- GetAutoDisplay()
  - TODO: return something like 'tmux'

- `.spacetea` layout:
  - JSON
  - "." key for whole project config, "<filename>" key for per-file config
  - each entry is a LIST OF DICTS which may have the following keys:
    - "strategy": (mandatory) one of 'command', 'pytest'
    - "command": the shell command to be executed if strategy is 'command'. Can
      be a string, or list of items to be shell-escaped
    - "pytest_args": a list of options to be passed to the py.test flag
      when stragety is 'pytest'

- g:spacetea_display
  - tells `:SpaceTea test` where to where to
  - where to 


- SOME CONCEPTS
  - "preview": where to show the tests while they are running. Options are
    - NULL: tests aren't shown anywhere while they're running
    - "tmux:SESSION[:WINDOW]" tests will be shown in a new window (or the
      window named WINDOW) of tmux session SESSION. The window will be given
      focus while the tests are running. The window will remain open after the
      tests have completed. The same window will be re-used for subsequent
      runs. A new pane is created for
      each file_or_dir that gets tested in the current run.
  - "examine": where to view tests after they have completed Options are
    - NULL: don't open the tests anywhere - just show a message stating that
      tests failed. If you had a "preview" set to tmux you should be able to
      see the test output there.
    - "tab:split": open test output in a new vim tab; :split horizontally for each
      separate output.
    - "right": open test output in a new vim window in the current tab which is
      right-maximized and then :split for each output.
