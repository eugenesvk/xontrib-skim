"""
skim (fuzzy finder) integration
"""
import subprocess
import re
import typing
from os                              	import environ, chdir  #
from pathlib                         	import Path     #
from xonsh.built_ins                 	import XSH
from prompt_toolkit.keys             	import ALL_KEYS
from xonsh.completers.path           	import complete_dir, _quote_paths
from xonsh.parsers.completion_context	import CompletionContextParser

__all__ = ()

envx    	= XSH.env or {}
env     	= environ
historyx	= XSH.aliases["history"]
eventx  	= XSH.builtins.events
cdx     	= XSH.aliases["cd"]
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

def skim_get_args(event, data_type): # get a list of skim arguments, combining defaults with user config
  buf = event.current_buffer
  if type(data_type) == str:
    data_type = [data_type]

  _def_opt   	= envx.get('SKIM_DEFAULT_OPTIONS'  	, None)
  _height    	= envx.get('SKIM_TMUX_HEIGHT'      	, '40%')
  _key_sort  	= envx.get('X_SKIM_KEY_SORT_TOGGLE'	, 'ctrl-r')
  _key_custom	= envx.get('X_SKIM_KEY_CUSTOM'     	, None)
  _no_height 	= envx.get('X_SKIM_NO_HEIGHT'      	, True)
  _no_sort   	= envx.get('X_SKIM_NO_SORT'        	, True)

  skim_args = [
    "--layout=reverse"	, # display from the |default|=bottom ¦reverse¦=top ¦reverse-list¦ top+prompt@bottom
    "--tiebreak=index"	, # Comma-separated list of sort criteria to apply when the scores are tied
      # score         	    Score of the fuzzy match algorithm
      # index         	    Prefers line that appeared earlier in the input stream
      # begin         	    Prefers line with matched substring closer to the beginning
      # end           	    Prefers line with matched substring closer to the end
      # length        	    Prefers line with shorter length
      # -XXX          	    negates XXX
  ]

  if   _key_sort:
    skim_args += [
      f"--bind={_key_sort}:toggle-sort",
    ]

  if   _key_custom and type(_key_custom) == dict:
    _key_opt = ",".join([f"{k}:{v}" for k,v in _key_custom.items()])
    skim_args += [
      f"--bind={_key_opt}",
    ]

  if   'history' in data_type:
    skim_args += [
      "--read0"	, # Read input delimited by NUL instead of ␤
      "--tac"  	, # reverse the order of the search result (normally used together with --no-sort)
    ]
    if 'cd'     in data_type:
      skim_args += ["--no-multi"] # disable multi-select, only 1 Dir can be cd'ed to
    else:
      skim_args += [   "--multi"]
    if     _no_sort:
      skim_args += [
        "--no-sort"	, # don't sort the search result (normally used together with --tac)
      ]
    if len(user_input := buf.text) > 0:
      skim_args += [f"--query=^{user_input}"] # add existing user input as initial query
  elif 'zoxide' in data_type: #
    skim_args += [
      "--delimiter=[^\t\n ][\t\n ]+"	, # field delimiter regex for --nth (default: AWK-style)
      "-n2.."                       	, # limit search scope from field#2 to the last
    ]
    if 'cd'     in data_type:
      skim_args += ["--no-multi"] # disable multi-select, only 1 Dir can be cd'ed to
    else:
      skim_args += [   "--multi"]
  elif 'ssh' in data_type:
    skim_args += [
      "--read0"   	, # Read input delimited by NUL instead of ␤
      "--no-multi"	, # disable multi-select, only 1 host can be ssh'ed to
    ]

  if ('file' in data_type) or\
     ('dir'  in data_type):
    skim_args += ["--keep-right"] # (for long paths) keep the right end visible
  if ('dir'  in data_type):
    if (preview := envx.get("X_SKIM_DIR_VIEW",None)):
      skim_args += [f"--preview={preview}"] #

  if 'freq' in data_type:
    skim_args += [
      "--delimiter=[^\t\n ][\t\n ]+"	, # field delimiter regex for --nth (default: AWK-style)
      "-n2.."                       	, # limit search scope from field#2 to the last
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

def skim_proc_run(event,data_type,env=envx): # Run a skim process with default args and return it
  if not (bin := get_bin(base)):
    return
  args = skim_get_args(event,data_type)
  skim_cmd = [bin] + args
  skim_proc = subprocess.run(  skim_cmd,            stdout=PIPE, text=True, env=env)
  return skim_proc

def skim_proc_open(event,data_type): # Create a skim process with default args and return it
  if not (bin := get_bin(base)):
    return
  args = skim_get_args(event,data_type)
  skim_cmd = [bin] + args
  skim_proc = subprocess.Popen(skim_cmd, stdin=PIPE,stdout=PIPE, text=True)
  return skim_proc

def skim_proc_close(event, skim_proc, prefix="", re_deprefix=None, replace=True, func=None): # Close the given skim process and reset shell
  skim_proc.stdin.close()
  skim_proc.wait()

  event.cli.renderer.erase() # clear old output

  buf = event.current_buffer
  if (skim_out := skim_proc.stdout.read().strip()):
    if re_deprefix:
      skim_out = re_deprefix.sub('',skim_out)
    if prefix:
      skim_out = prefix +' '+ skim_out

    if func:
      func(event, skim_out)
    elif replace:
      buf.text           	=     skim_out
      buf.cursor_position	= len(skim_out)
    else:
      buf.insert_text(skim_out.strip())

def skim_get_history_cmd(event): # Run skim, pipe xonsh cmd history to it, get the chosen item printed to stdout
  data_type = ['history']
  if (freq := envx.get("X_SKIM_CMD_FRQ",True)):
    data_type += ['freq']
  skim_proc = skim_proc_open(event, data_type)
  re_deprefix = None
  if freq:
    if (histx := XSH.history) is None:
      return
    re_deprefix = re_zoxide_index
    cmds_processed = dict()
    for entry in histx.all_items():
      if   (cmd   := entry.get("inp")):
        if (cmd_f := entry.get("frequency")):
          cmds_processed[cmd.strip()] = cmd_f
        else:
          cmds_processed[cmd.strip()] = 0
    _pad_freq = len(str(max(cmds_processed.values())))
    _min = int(envx.get("X_SKIM_CMD_FRQ_MIN",5))
    for k,v in cmds_processed.items():
      if v >= _min:
        skim_proc.stdin.write(f"{str(v).rjust(_pad_freq)} {k}\0")
      else:
        skim_proc.stdin.write(f"{    ''.rjust(_pad_freq)} {k}\0")
  else:
    historyx(args=["show","--null-byte","xonsh"], stdout=skim_proc.stdin) # 'xonsh' session separated by null
  skim_proc_close(event, skim_proc, re_deprefix=re_deprefix, replace=True)

def skim_get_history_cwd(event, cd=False): # Run skim, pipe xonsh CWD history to it, get the chosen item(s) printed to stdout OR cd to a single chosen item
  if (histx := XSH.history) is None:
    return
  data_type = ['history','dir']
  if cd:
    data_type += ['cd']
  if (freq := envx.get("X_SKIM_CWD_FRQ",True)):
    data_type += ['freq']
  skim_proc = skim_proc_open(event, data_type)
  re_deprefix = None
  if freq:
    re_deprefix = re_zoxide_index
    cwds_processed = dict()
    cwd_count = 0
    for entry in histx.all_items():
      cwd_count += 1
      if (cwd := entry.get("cwd")):
        if cwd in cwds_processed:
          cwds_processed[cwd]['id']   = cwd_count
          cwds_processed[cwd]['freq'] += 1
        else:
          cwds_processed[cwd] = {'id':cwd_count, 'freq':1}
    _pad_freq = len(str(max([v['freq'] for v in cwds_processed.values()])))

    cwds_by_id = dict()
    for k,v in cwds_processed.items():
      cwds_by_id[v['id']] = {'path':k, 'freq':v['freq']}
    cwds_sorted = dict(sorted(cwds_by_id.items()))
    _min = int(envx.get("X_SKIM_CWD_FRQ_MIN",5))
    for k,v in cwds_sorted.items():
      if v['freq'] >= _min:
        skim_proc.stdin.write(f"{str(v['freq']).rjust(_pad_freq)} {v['path']}\0")
      else:
        skim_proc.stdin.write(f"{            ''.rjust(_pad_freq)} {v['path']}\0")
  else:
    cwds_processed = set()
    for entry in histx.all_items():
      if (cwd := entry.get("cwd")) and\
         (cwd not in cwds_processed):
        cwds_processed.add(cwd)
        skim_proc.stdin.write(f"{cwd}\0")
  if cd:
    skim_proc_close(event, skim_proc, re_deprefix=re_deprefix, func=_on_close_cd_inline      , replace=False)
  else:
    skim_proc_close(event, skim_proc, re_deprefix=re_deprefix, func=_on_close_paths_multiline, replace=False)

from xonsh.style_tools import partial_color_tokenize
from prompt_toolkit.formatted_text import PygmentsTokens
from xonsh.ptk_shell.shell import tokenize_ansi
def _p_msg_fmt(s):
  return tokenize_ansi(PygmentsTokens(partial_color_tokenize(XSH.shell.shell.prompt_formatter(s))))

import threading
def _update_prompt(): # force-update all 3 prompts (if exist) to the newer values. Helpful when xontrib changes some prompt variables in the background and doesn't want to wait for the next prompt cycle
  shellx = XSH.shell.shell
  shellx.prompt_formatter.fields.reset() # reset fields cache
  if prompt_l := envx['PROMPT']:
    prompt_l = prompt_l() if callable(prompt_l) else prompt_l
    shellx.prompter.message        = _p_msg_fmt(prompt_l)
  if prompt_r := envx['RIGHT_PROMPT']:
    prompt_r = prompt_r() if callable(prompt_r) else prompt_r
    shellx.prompter.rprompt        = _p_msg_fmt(prompt_r)
  if prompt_b := envx['BOTTOM_TOOLBAR']:
    prompt_b = prompt_b() if callable(prompt_b) else prompt_b
    shellx.prompter.bottom_toolbar = _p_msg_fmt(prompt_b)
  shellx.prompter.app.invalidate()      # send signal that prompt needs update

def _on_close_cd_inline(event, path: typing.Optional[typing.AnyStr] = None) -> None:
  """Change dir without creating a new prompt line, updating existing instead"""
  buf = event.current_buffer
  doc = buf.document
  cli = event.cli

  if path is None:
    args = []
  elif isinstance(path, bytes):
    args = [path.decode("utf-8")]
  elif isinstance(path, str):
    args = [path]
  if         path and \
    not Path(path).is_dir():
    return # do nothing is target is not a Dir
  _, exc, _ = cdx(args)
  if exc is not None:
    raise Exception(exc)
  else:
    _text = doc.current_line_before_cursor
    buf.delete_before_cursor(len(_text))
    t = threading.Thread(target=_update_prompt, args=())
    t.start()
    buf.insert_text(_text.strip())

def _on_close_paths_multiline(event, paths, prefix=""):  # todo: replace _internal _quote_paths
  buf	= event.current_buffer
  cmd	= ""
  for p in paths.splitlines():
    q_beg, q_end = "'", "'" # 'quote', ↓ with only ' in path switch "quote"
    if ("'"     in p.strip()) and \
       ('"' not in p.strip()):
      q_beg, q_end = '"', '"'
    cmd += _quote_paths([str(Path(prefix,p.strip()))], start=q_beg,end=q_end)[0].pop() + ' ' # ({'p'}, True) → [0].pop() → 'p'
  buf.insert_text(cmd.strip())


re_zoxide_index = re.compile(r'^[0-9. ]*', re.IGNORECASE|re.MULTILINE)
def skim_get_history_cwd_zoxide(event, cd=False): # Run skim, pipe zoxide dir history to it, get the chosen item printed to stdout
  if not (bin_ := get_bin('zoxide')):
    return
  args = ['query','-ls']
  zoxide_cmd = [bin_] + args

  data_type = ['zoxide','dir']
  if cd:
    data_type += ['cd']
  skim_proc = skim_proc_open(event, data_type)
  subprocess.run(zoxide_cmd, stdout=skim_proc.stdin, text=True)
  if cd:
    skim_proc_close(event, skim_proc, re_deprefix=re_zoxide_index, func=_on_close_cd_inline)
  else:
    skim_proc_close(event, skim_proc, re_deprefix=re_zoxide_index, func=_on_close_paths_multiline)

def get_dir_complete(line):
  ctx_parse	= CompletionContextParser().parse
  if (cmd := ctx_parse(line, len(line)).command).prefix:
    paths = complete_dir(cmd)[0]

    path = None
    if   len(paths) == 1: # if completes to a dir, use it
      path = Path(paths.pop().value).expanduser()
    elif len(paths)  > 1: # if already a dir and completes to subdirs, use main dir
      path = Path(paths.pop().value).parent.expanduser()

    if path and \
       path.is_dir():
        return path, cmd.prefix

  return "", ""

def skim_get_dir(event):
	skim_get_file(event, dirs_only=True)
def skim_get_file(event, dirs_only=False):
  buf          	= event.current_buffer

  # 1. if our string completes to a Dir, cd there to trick the finder to start search there
  # (a less sneaky alternative is to pass Dir as an explicit argument like '--full-path PATH', but that's tool-dependant)
  before_cursor	= buf.document.current_line_before_cursor
  cwd          	= None
  dir_complete, prefix = get_dir_complete(before_cursor)
  if (dir_complete):
    cwd = Path.cwd()
    chdir(dir_complete)

  # 2. run skim with our custom find file/dir commands
  env_override = {}
  if dirs_only:
    if "X_SKIM_CMD_FIND_DIR" in envx:
      env_override['SKIM_DEFAULT_COMMAND'] = envx["X_SKIM_CMD_FIND_DIR"]
  else:
    if "X_SKIM_CMD_FIND"      in envx:
      env_override['SKIM_DEFAULT_COMMAND'] = envx["X_SKIM_CMD_FIND"]
  with envx.swap(**env_override):
    skim_proc_res = skim_proc_run(event, 'file', env=envx.detype())
  choice = skim_proc_res.stdout.strip()

  # 3. cleanup
  if cwd: # switch back to our starting Dir
    chdir(cwd)
  event.cli.renderer.erase() # clear old output

  # 3. insert selected path(s), xonsh-quoted
  if choice:
    if dir_complete:
      buf.delete_before_cursor(len(prefix))
    _on_close_paths_multiline(event, choice, prefix=dir_complete)

re_Host = re.compile(r'Host\s+=?(.*)\n?', re.IGNORECASE)
def skim_get_ssh(event, dirs_only=False):
  buf	= event.current_buffer

  skim_proc = skim_proc_open(event, 'ssh')
  host_processed = set()
  ssh_src = ["~/.ssh/config", "/etc/ssh/ssh_config"]
  for ssh_file in ssh_src:
    if (p := Path(ssh_file).expanduser()).is_file():
      with p.open() as f:
        for line in f:
          if (match := re_Host.search(line)):
            if (hostname := match.group(1)) not in host_processed:
              host_processed.add(hostname)
              skim_proc.stdin.write(f"{hostname}\0")
  ssh_hist = ["~/.ssh/known_hosts"]
  for ssh_file in ssh_hist:
    if (p := Path(ssh_file).expanduser()).is_file():
      with p.open() as f:
        for line in f:
          if len(match := line.split(',')) > 1:
            if (hostname := match[0]) not in host_processed:
              host_processed.add(hostname)
              skim_proc.stdin.write(f"{hostname}\0")
  skim_proc_close(event, skim_proc, prefix='ssh', replace=True)


re_despace = re.compile(r'\s', re.IGNORECASE)
def skim_keybinds(bindings, **_): # Add skim keybinds (when use as an argument in eventx.on_ptk_create)
  from prompt_toolkit.key_binding.key_bindings import _parse_key

  _default_keys = {
    "X_SKIM_KEY_HIST"     	: "c-s",
    "X_SKIM_KEY_HIST_CWD→"	: ['escape','s'],
    "X_SKIM_KEY_HIST_CWD" 	: ['escape','c-s'],
    "X_SKIM_KEY_HIST_Z→"  	: ['escape','z'],
    "X_SKIM_KEY_HIST_Z"   	: ['escape','c-z'],
    "X_SKIM_KEY_FILE"     	: "c-f",
    "X_SKIM_KEY_DIR"      	: ['escape','f'],
    "X_SKIM_KEY_SSH"      	: "c-b",
    }

  def handler(key_user_var):
    def skip(func):
      pass

    if envx.get('SHELL_TYPE') in ["prompt_toolkit", "prompt_toolkit2"]:
      bind_add = bindings.add
    else:
      bind_add = bindings.registry.add_binding

    key_user = envx.get(     key_user_var, None)
    key_def  = _default_keys[key_user_var]
    if   key_user == None:     # doesn't exist       → use default
      if type(key_def) == list:
        return bind_add(*key_def)
      else:
        return bind_add( key_def)
    elif key_user == False:    # exists and disabled → don't bind
      return skip
    else:                      # remove whitespace
      key_user = re_despace.sub('',key_user)

    _controls = ['⎈','⌃']
    for ctrl in _controls:
      if ctrl in key_user: # replace ctrl symbols with ptk names
        key_user = key_user.replace(ctrl,'c-')
    _alts = ['a-','⌥','⎇']
    for alt in _alts:
      if alt in key_user: # replace alt with an ⎋ sequence of keys
        key_user = ['escape', key_user.replace(alt,'')]
        break

    if   type(key_user) == str  and\
         key_user in ALL_KEYS: # exists and   valid  → use it
      return bind_add(key_user)
    elif type(key_user) == list and\
      all(k in ALL_KEYS or _parse_key(k) for k in key_user):
      return bind_add(*key_user)
    else:                      # exists and invalid  → use default
      print_color("{BLUE}xontrib-skim:{RESET} your "+key_user_var+" '{BLUE}"+str(key_user)+"{RESET}' is {RED}invalid{RESET}; "+\
        "using the default '{BLUE}"+str(key_def)+"{RESET}'; run ↓ to see the allowed list\nfrom prompt_toolkit.keys import ALL_KEYS; print(ALL_KEYS)")
      if type(key_def) == list:
        return bind_add(*key_def)
      else:
        return bind_add( key_def)

  @handler("X_SKIM_KEY_HIST")
  def skim_history_cmd(event): # Search in history entries and insert the chosen command
    skim_get_history_cmd(event)
  @handler("X_SKIM_KEY_HIST_CWD→")
  def skim_history_cwd(event): # Search in history entries' CWD and CD to the selected item
    skim_get_history_cwd(event, cd=True)
  @handler("X_SKIM_KEY_HIST_CWD")
  def skim_history_cwd(event): # Search in history entries' CWD and insert the selected item(s)
    skim_get_history_cwd(event, cd=False)
  @handler("X_SKIM_KEY_HIST_Z→")
  def skim_history_cwd_zoxide(event): # Search in zoxide's history entries and CD to the selected item
    skim_get_history_cwd_zoxide(event, cd=True)
  @handler("X_SKIM_KEY_HIST_Z")
  def skim_history_cwd_zoxide(event): # Search in zoxide's history entries and insert the selected item(s)
    skim_get_history_cwd_zoxide(event, cd=False)

  @handler("X_SKIM_KEY_FILE")
  def skim_file(event): # Find files in the current directory and its sub-directories
    skim_get_file(event)
  @handler("X_SKIM_KEY_DIR")
  def skim_dir(event):  # Find dirs  in the current directory and its sub-directories
    skim_get_dir(event)

  @handler("X_SKIM_KEY_SSH")
  def skim_ssh(event):  # Run 'ssh HOST' for hosts in /etc/ssh/ssh_config, ~/.ssh/config, ~/.ssh/known_hosts
    skim_get_ssh(event)


def _activate_skim():
  if (bin := get_bin(base)):           	# if skim exists register events↓
    eventx.on_ptk_create(skim_keybinds)	# add custom skim keybinds

_activate_skim()
