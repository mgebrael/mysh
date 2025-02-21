"""
Module to handle finding and executing files located on the PATH.
"""
import sys
import os

def find_path(path: str, command: str) -> str | bool:
    '''
    Returns path if it has executable permissions, True if path exists, False otherwise.
    '''
    for p in path.split(":"):
        if os.path.exists(f"{p}/{command}") and os.access(f"{p}/{command}", os.X_OK):
            return os.path.abspath(f"{p}/{command}")
        if os.path.exists(f"{p}/{command}"):
            return True
    return False

def run_command(tokens: list[str], environment_variables: dict[str, str], redirect=None) -> None:
    '''
    Runs the given executable found on the PATH.
    '''
    first_token = tokens[0]
    if redirect == None:
        redirect = 1

    try:
        path = environment_variables["PATH"]
    except KeyError:
        path = os.defpath

    if first_token[0] == "/":
        executable_path = find_path("/", first_token)
        if isinstance(executable_path, str) is False and executable_path is False:
            print("mysh: no such file or directory:", first_token, file=sys.stderr)
            return
    elif "/" in first_token:
        executable_path = find_path(environment_variables["PWD"], first_token)
        if isinstance(executable_path, str) is False and executable_path is False:
            print("mysh: no such file or directory:", first_token, file=sys.stderr)
            return
    else:
        executable_path = find_path(path, first_token)

    if isinstance(executable_path, str) is False and executable_path is True:
        print("mysh: permission denied:", first_token, file=sys.stderr)
        return
    if isinstance(executable_path, str) is False and executable_path is False:
        print("mysh: command not found:", first_token, file=sys.stderr)
        return
    if isinstance(executable_path, str) and os.path.isdir(executable_path) is True:
        print("mysh: is a directory:", first_token, file=sys.stderr)
        return

    pid = os.fork()
    if pid == 0: # Child
        # Set the process group of the child process to a brand new one
        os.setpgid(0, 0)
        os.dup2(redirect, 1)
        try:
            os.execvp(executable_path, tokens)
        except PermissionError:
            print("mysh: permission denied:", first_token, file=sys.stderr)
            exit()

    elif pid > 0: # Parent
        # Also try to create a new process group for the child process
        try:
            os.setpgid(0, 0)
        except PermissionError:
            # Child has already set new process group!
            pass

        child_pgid = os.getpgid(0) # get child's new process group id
        file_desc = os.open("/dev/tty", 0) # open current terminal device
        os.tcsetpgrp(file_desc, child_pgid)
        os.wait()
        os.tcsetpgrp(file_desc, os.getpgrp())
        os.close(file_desc)
