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
  # config var                        	  value	  |default|alt_cmd¦ comment
  envx["XONTRIB_SKIM_KEY_HISTORY"]    	= "c-r" # |c-r|False¦ ⌃R Search in history entries and insert the chosen command
  envx["XONTRIB_SKIM_KEY_HISTORY_CWD"]	= "c-t" # |c-t|False¦ ⌃T Search in history entries' CWD and insert the chosen command
  envx["XONTRIB_SKIM_KEY_FILE"]       	= "c-g" # |c-g|False¦ ⌃G Find files in the current directory and its sub-directories
  envx["XONTRIB_SKIM_KEY_DIR"]        	= "c-b" # |c-b|False¦ ⌃B Find dirs  in the current directory and its sub-directories
  envx["XONTRIB_SKIM_KEY_SSH"]        	= "c-s" # |c-s|False¦ ⌃S Search in /etc/ssh/ssh_config or ~/.ssh/config items and issue ssh command on the chosen item
  # run to see the allowed list for ↑: from prompt_toolkit.keys import ALL_KEYS; print(ALL_KEYS)
  # ↓ are key bindings for the skim binary itself, not this xontrib, so use skim rules https://github.com/lotabout/skim#keymap
  envx["XONTRIB_SKIM_KEY_SORT_TOGGLE"]	= "ctrl-r" # |ctrl-r| ⌃R binding for 'toggle-sort'
  envx["XONTRIB_SKIM_NO_HEIGHT"]      	= True # |True|False¦ disable `--height` to fix a skim bug
  envx["XONTRIB_SKIM_NO_SORT"]        	= True # |True|False¦ disable history sorting
  # envx["XONTRIB_SKIM_CMD_FIND"]     	= "fd -t f -t l -c never" # |None| command used by skim to search for files
  # envx["XONTRIB_SKIM_CMD_FIND_DIR"] 	= "fd -t d      -c never" # |None| command used by skim to search for directories
  # envx["SKIM_DEFAULT_OPTIONS"]      	= "" # |None| other options to pass to skim

xontribs_load(xontribs_manual) # actually load all xontribs in the list
```

2. Or just add this to your xonsh run control file
```xsh
xontrib load skim # Initializes skim (fuzzy finder)
# configure like in the example above, but replace envx['VAR'] with $VAR
$XONTRIB_SKIM_KEY_HISTORY	= "c-r" # ...
```

## Examples

...

## Known issues

...

## Credits

This package was created with [xontrib template](https://github.com/xonsh/xontrib-template)
