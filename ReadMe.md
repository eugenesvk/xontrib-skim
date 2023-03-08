<p align="center">
skim (fuzzy finder) integration
<br>
(description continued)
</p>

<p align="center">  
description continued
</p>


## Installation

To install use pip:

```xsh
xpip install xontrib-skim
# or: xpip install -U git+https://github.com/eugenesvk/xontrib-skim
```

## Usage

This xontrib requires `sk` (or `sk-tmux`) to be in `PATH`. If it's added to `PATH` via another xontrib (e.g, you installed it via Homebrew and use `xontrib-homebrew`), then you should load this xontrib after the one setting `PATH`

1. Add the following to your `.py` xontrib loading config and `import` it in your xonsh run control file (`~/.xonshrc` or `~/.config/rc.xsh`):
```py
from xonsh.xontribs 	import xontribs_load
from xonsh.built_ins	import XSH
envx = XSH.env

xontribs = [ "skim", # Initializes skim (polyglot asdf-like runtime manager)
 # your other xontribs
]
# ↓ optional configuration variables (use `False` to disable a keybind)
if 'skim' in xontribs: # Configure skim only if you're actually loading it
  # config var                	  value		 |default|alt_cmd¦ comment
  envx["X_SKIM_KEY_HIST"]     	= "⎈s" 		#|c-s|             False¦ Search in history entries and insert the chosen command
  envx["X_SKIM_KEY_HIST_CWD→"]	= "⎇s" 		#|['escape','s']|  False¦ Search in history entries' CWD and CD to the selected item (if exists, do nothing otherwise)
  envx["X_SKIM_KEY_HIST_CWD"] 	= "⎈⎇s"	#|['escape','c-s']|False¦ Search in history entries' CWD and insert the selected item(s)
  envx["X_SKIM_KEY_HIST_Z→"]  	= "⎇z" 		#|['escape','z']|  False¦ Search in zoxide's history entries and CD to the selected item (if exists, do nothing otherwise)
  envx["X_SKIM_KEY_HIST_Z"]   	= "⎈⎇z"	#|['escape','c-z']|False¦ Search in zoxide's history entries and insert the selected item(s)
  envx["X_SKIM_KEY_FILE"]     	= "⎈f" 		#|c-f|             False¦ Find files in the current directory and its sub-directories
  envx["X_SKIM_KEY_DIR"]      	= "⎇f" 		#|['escape','f']|  False¦ Find dirs  in the current directory and its sub-directories
  envx["X_SKIM_KEY_SSH"]      	= "⎈b" 		#|c-b|             False¦ Run 'ssh HOST' for hosts in /etc/ssh/ssh_config, ~/.ssh/config, ~/.ssh/known_hosts
  # run to see the allowed list for ↑: from prompt_toolkit.keys import ALL_KEYS; print(ALL_KEYS)
  # Alt is also supported as either of: a- ⎇ ⌥ (converted to a prefix 'escape')
  # Control symbols are also supported as either of: ⎈ ⌃
  # ↓ are key bindings for the skim binary itself, not this xontrib, so use skim rules https://github.com/lotabout/skim#keymap
  envx["X_SKIM_KEY_SORT_TOGGLE"]	= "ctrl-r"	#|ctrl-r|False¦ ⎈R binding for 'toggle-sort'
  envx["X_SKIM_KEY_CUSTOM"]     	= None    	#|None| a dictionary of {'key':'action'}
  envx["X_SKIM_NO_HEIGHT"]      	= True    	#|True|False¦ disable `--height` to fix a skim bug
  envx["X_SKIM_NO_SORT"]        	= True    	#|True|False¦ disable history sorting
  # envx["X_SKIM_CMD_FIND"]     	= "fd -t f -t l -c never" # |None| command used by skim to search for files
  # envx["X_SKIM_CMD_FIND_DIR"] 	= "fd -t d      -c never" # |None| command used by skim to search for directories
  # envx["SKIM_DEFAULT_OPTIONS"]	= "" # |None| other options to pass to skim

xontribs_load(xontribs_manual) # actually load all xontribs in the list
```

2. Or just add this to your xonsh run control file
```xsh
xontrib load skim # Initializes skim (fuzzy finder)
# configure like in the example above, but replace envx['VAR'] with $VAR
$X_SKIM_KEY_HISTORY	= "c-s" # ...
```

## Examples

...

## Known issues

- skim doesn't clear the screen properly when `--height` is set due to a [bug](https://github.com/lotabout/skim/issues/494). At the moment this flag is disabled via `X_SKIM_NO_HEIGHT`
- skim sometimes prints extraneous text symbols, e.g., when searching history, maybe due to [this bug](https://github.com/lotabout/skim/issues/502) or something else
- skim might bug in tmux on some system/terminals [bug1](https://github.com/lotabout/skim/issues/482), [bug2](https://github.com/lotabout/skim/issues/412) 
- `toggle-sort` (and `X_SKIM_KEY_SORT_TOGGLE`) doesn't seem to be supported in skim, `ls | sk --bind=pgdn:toggle-sort` also fails
- to remove extra `?[38;5;26mFOLDER` from output, add `--ansi` to `$SKIM_DEFAULT_OPTIONS` or disable colors in your `$X_SKIM_CMD_FIND`/`DIR` filter (e.g., `fd -t d -c never`)
- <kbd>⎈</kbd>/<kbd>⎇</kbd><kbd>f</kbd> conflict with [xontrib-output-search](https://github.com/anki-code/xontrib-output-search)'s defaults

## Credits

This package was created with [xontrib template](https://github.com/xonsh/xontrib-template)
