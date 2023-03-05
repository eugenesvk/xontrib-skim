"""
skim (fuzzy finder) integration
"""
import subprocess
from os                 	import environ  #
from pathlib            	import Path     #
from xonsh.built_ins    	import XSH
from prompt_toolkit.keys	import ALL_KEYS

__all__ = ()

envx    	= XSH.env or {}
env     	= environ
historyx	= XSH.aliases["history"]
eventx  	= XSH.builtins.events
PIPE    	= subprocess.PIPE

base={'':'sk', 'tmux':'sk-tmux'}

is_cmd_cache_fresh = False
def get_bin(base_in): # (lazily 1st) get the full path to skim binary from xonsh binary cache
  if type(base_in) == dict:
    if 'tmux' in base_in and envx.get("TMUX", ""):
      base = base_in['tmux']
    else:
      base = base_in['']
  else:
    base = base_in

  global is_cmd_cache_fresh
  bin   = XSH.commands_cache.lazy_locate_binary(base, ignore_alias=True)
  if not bin and not is_cmd_cache_fresh:
    is_cmd_cache_fresh = True
    bin = XSH.commands_cache.     locate_binary(base, ignore_alias=True)
  if not bin:
    PATH = envx.get("PATH")
    print(f"Cannot find '{base}' in {PATH}")
    return None
  else:
    return bin

def skim_get_args(): # get a list of skim arguments, combining defaults with user config
  _def_opt  	= envx.get('SKIM_DEFAULT_OPTIONS'         	, None)
  _height   	= envx.get('SKIM_TMUX_HEIGHT'             	, '40%')
  _key_sort 	= envx.get('XONTRIB_SKIM_KEY_HISTORY_SORT'	, 'ctrl-r')
  _no_height	= envx.get('XONTRIB_SKIM_NO_HEIGHT'       	, True)

  skim_args = [
    "--read0"         	, # Read input delimited by NUL instead of ␤
    "--layout=reverse"	, # display from the |default|=bottom ¦reverse¦=top ¦reverse-list¦ top+prompt@bottom
    "--tiebreak=index"	, # Comma-separated list of sort criteria to apply when the scores are tied
      # score         	    Score of the fuzzy match algorithm
      # index         	    Prefers line that appeared earlier in the input stream
      # begin         	    Prefers line with matched substring closer to the beginning
      # end           	    Prefers line with matched substring closer to the end
      # length        	    Prefers line with shorter length
      # -XXX          	    negates XXX
    "--tac"           	, # reverse the order of the search result (normally used together with --no-sort)
    "--no-sort"       	, # don't sort the search result (normally used together with --tac)
    "--no-multi"      	, # disable multi-select
    f"--bind={_key_sort}:toggle-sort",
  ]

  if not _no_height: # todo: move ↑ after https://github.com/lotabout/skim/issues/494 is fixed
    skim_args += [
      f"--height={_height}"	, # display sk window below the cursor with the given height instead of using the full screen
    ]

  if _def_opt: # add default options from the environment
    if   type(_def_opt) == str:
      skim_args += _def_opt.split(' ')
    elif type(_def_opt) == list:
      skim_args += _def_opt

  return skim_args

def skim_proc_open(event): # Create a skim process with default arguments and return it
  if not (bin := get_bin(base)):
    return
  args = skim_get_args()

  buf = event.current_buffer
  if len(user_input := buf.text) > 0:
    args += [f"--query=^{user_input}"] # add existing user input as initial query

  skim_cmd = [bin] + args
  skim_proc = subprocess.Popen(skim_cmd, stdin=PIPE,stdout=PIPE, text=True)

  return skim_proc

def skim_proc_close(skim_proc, event): # Close the given skim process and reset shell
  skim_proc.stdin.close()
  skim_proc.wait()

  event.cli.renderer.erase() # clear old output

  buf = event.current_buffer
  if (skim_out := skim_proc.stdout.read().strip()):
    buf.text           	= skim_out
    buf.cursor_position	= len(skim_out)

def skim_get_history_cmd(event): # Run skim, pipe xonsh cmd history to it, get the chosen item printed to stdout
  skim_proc = skim_proc_open(event)
  historyx(args=["show","--null-byte","xonsh"], stdout=skim_proc.stdin) # 'xonsh' session separated by null
  skim_proc_close(skim_proc, event)

def skim_get_history_cwd(event): # Run skim, pipe xonsh CWD history to it, get the chosen item printed to stdout
  if (histx := XSH.history) is None:
    return
  skim_proc = skim_proc_open(event)
  cwds_processed = set()
  for entry in histx.all_items():
    if (cwd := entry.get("cwd")) and\
       (cwd not in cwds_processed):
      cwds_processed.add(cwd)
      skim_proc.stdin.write(f"{cwd}\0")
  skim_proc_close(skim_proc, event)


def skim_keybinds(bindings, **_): # Add skim keybinds (when use as an argument in eventx.on_ptk_create)
  _default_keys = {
    "XONTRIB_SKIM_KEY_HISTORY"	:"c-r",
    "XONTRIB_SKIM_KEY_SSH"    	:"c-s",
    "XONTRIB_SKIM_KEY_FILE"   	:"c-g",
    "XONTRIB_SKIM_KEY_DIR"    	:"c-b",
    "XONTRIB_SKIM_KEY_HISTORY_CWD"	:"c-t",
    }

  def handler(key_user_var):
    def skip(func):
      pass

    key_user = envx.get(     key_user_var, None)
    key_def  = _default_keys[key_user_var]
    if   key_user == None:     # doesn't exist       → use default
      return bindings.add(key_def)
    elif key_user == False:    # exists and disabled → don't bind
      return skip
    elif key_user in ALL_KEYS: # exists and   valid  → use it
      return bindings.add(key_user)
    else:                      # exists and invalid  → use default
      print_color("{BLUE}xontrib-skim:{RESET} your "+key_user_var+" '{BLUE}"+key+"{RESET}' is {RED}invalid{RESET}; "+\
        "using the default '{BLUE}"+key_def+"{RESET}'; run ↓ to see the allowed list\nfrom prompt_toolkit.keys import ALL_KEYS; print(ALL_KEYS)")
      return bindings.add(key_def)

  @handler("XONTRIB_SKIM_KEY_HISTORY")
  def skim_history_cmd(event): # Search in history entries and insert the chosen command
    skim_get_history_cmd(event)
  @handler("XONTRIB_SKIM_KEY_HISTORY_CWD")
  def skim_history_cwd(event): # Search in dir history entries and insert the chosen command
    skim_get_history_cwd(event)



def _activate_skim():
  if (bin := get_bin(base)):           	# if skim exists register events↓
    eventx.on_ptk_create(skim_keybinds)	# add custom skim keybinds

_activate_skim()
