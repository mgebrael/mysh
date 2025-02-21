"""
Module containing built-in commands for mysh.
"""
import sys
import os
import re
import parsing
import seeker
import mysh

def exitsh(tokens: list[str]) -> bool:
    '''
    Exit command: exits the shell.
    Optional argument: integer exit code.
    '''
    if len(tokens) >= 3:
        print("exit: too many arguments", file=sys.stderr)
        return False
    if len(tokens) == 1:
        return True

    if tokens[1].isdigit() is False:
        print("exit: non-integer exit code provided:", tokens[1], file=sys.stderr)
        return False

    sys.exit(int(tokens[1]))
    return True

def pwdsh(tokens: list[str], environment_variables: dict[str, str], output=sys.stdout) -> None:
    '''
    PWD command: prints the working directory.
    Optional flag -P: resolves symbollic links.
    '''
    working_directory = environment_variables["PWD"]
    symbolic_link = False

    if len(tokens) == 1:
        print(working_directory, file=output)
        return

    for args in tokens[1:]:
        if args[0] != '-':
            print("pwd: not expecting any arguments", file=sys.stderr)
            return
        for flag in args[1:]:
            if flag != 'P':
                print(f"pwd: invalid option: -{flag}", file=sys.stderr)
                return
        symbolic_link = True

    if symbolic_link:
        print(os.path.realpath(working_directory), file=output)
    else:
        print(working_directory, file=output)

def cdsh(tokens: list[str], environment_variables: dict[str, str]) -> None:
    '''
    CD command: change directories.
    '''
    if len(tokens) == 1 or tokens[1] == "~":
        environment_variables["PWD"] = "/home"
        os.chdir("/home")
        return
    if len(tokens) > 2:
        print("cd: too many arguments", file=sys.stderr)
        return

    new_path = tokens[1]

    if os.path.exists(new_path) is False:
        print("cd: no such file or directory:", new_path, file=sys.stderr)
        return
    if os.path.isdir(new_path) is False:
        print("cd: not a directory:", new_path, file=sys.stderr)
        return

    if new_path[0] != "/":
        new_path = os.path.abspath(environment_variables["PWD"] + f"/{new_path}")

    # behaviour for bad permission
    if os.access(new_path, os.R_OK) is False:
        print("cd: permission denied:", new_path, file=sys.stderr)
        return

    os.chdir(new_path)
    environment_variables["PWD"] = new_path

def whichsh(tokens: list[str], environment_variables: dict[str, str], output=sys.stdout) -> None:
    '''
    Which command: prints the location of the given executable(s).
    '''
    if len(tokens) == 1:
        print("usage: which command ...", file=sys.stderr)
        return

    try:
        path = environment_variables["PATH"]
    except:
        path = os.defpath

    for command in tokens[1:]:
        executable_path = seeker.find_path(path, command)

        if command in ['var', 'pwd', 'cd', 'which', 'exit']:
            print(f"{command}: shell built-in command", file=output)
        elif isinstance(executable_path, str) and os.path.isdir(executable_path) is False:
            print(executable_path, file=output)
        else:
            print(command, "not found", file=output)

def varsh(tokens: list[str], environment_variables: dict[str, str]) -> None:
    '''
    Var command: sets new shell variables.
    '''
    if len(tokens) == 1:
        print("var: expected 2 arguments, got 0", file=sys.stderr)
        return

    arg1 = tokens[1]
    if arg1[0] == '-':
        for flag in arg1[1:]:
            if flag != 's':
                print(f"var: invalid option: -{flag}", file=sys.stderr)
                return

        # var with -s
        if len(tokens) != 4:
            print("var: expected 2 arguments, got", len(tokens) - 2, file=sys.stderr)
            return

        if re.search("[^A-Za-z0-9_]", tokens[2]) is not None:
            print("var: invalid characters for variable", tokens[2], file=sys.stderr)
            return

        fd_read, fd_write = os.pipe()
        mysh.run_shell(environment_variables, tokens[3], fd_write, True)

        command_output = open(fd_read)
        variable_value = "".join(command_output.readlines())
        environment_variables[tokens[2]] = variable_value
        command_output.close()

    else:
        if len(tokens) != 3:
            print("var: expected 2 arguments, got", len(tokens) - 1, file=sys.stderr)
            return

        if re.search("[^A-Za-z0-9_]", arg1) != None:
            print("var: invalid characters for variable", arg1, file=sys.stderr)
            return

        environment_variables[arg1] = tokens[2]
