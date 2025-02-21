import signal
import shlex
import sys
import os
import parsing
import seeker
import setter
import mycmd

# DO NOT REMOVE THIS FUNCTION!
# This function is required in order to correctly switch the terminal foreground group to
# that of a child process.
def setup_signals() -> None:
    """
    Setup signals required by this program.
    """
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)

def run_shell(environment_variables: dict[str, str], input_from_pipe: str = None,
              output_fd: int = None, pipe: bool = False) -> None:
    '''
    Run the shell, and continually display new prompts.
    '''
    while True:
        prompt = environment_variables['PROMPT']

        if input_from_pipe == None:
            input_prompt = input(prompt)
        else:
            input_prompt = input_from_pipe
        if output_fd == None:
            output = sys.stdout
        else:
            output = open(output_fd, "w")

        line = setter.substitute_variables(input_prompt, environment_variables)
        if type(line) != str:
            continue

        # piping
        split_by_pipe = parsing.split_by_pipe_op(line)
        fd_cp = os.dup(0)

        for command_group in split_by_pipe:
            if len(split_by_pipe) > 1 and command_group.strip() == "":
                print("mysh: syntax error: expected command after pipe", file=sys.stderr)
                split_by_pipe = [""]
                break

        while len(split_by_pipe) > 1:
            fd_read, fd_write = os.pipe()
            pipe_segment = split_by_pipe.pop(0)

            run_shell(environment_variables, pipe_segment, fd_write, True)
            os.dup2(fd_read, 0)

        line = split_by_pipe[0]

        # shlex analyzer for splitting a line into arguments
        analyzer = shlex.shlex(line, posix=True)
        analyzer.escapedquotes = '"\''
        analyzer.whitespace_split = True

        try:
            tokens = list(analyzer)
        except ValueError:
            print("mysh: syntax error: unterminated quote", file=sys.stderr)
            continue

        if tokens == []:
            continue
        first_token = tokens[0]
        parsing.parse_home(tokens, environment_variables)

        if first_token == 'exit':
            if mycmd.exitsh(tokens):
                break
        elif first_token == 'pwd':
            mycmd.pwdsh(tokens, environment_variables, output)
        elif first_token == 'cd':
            mycmd.cdsh(tokens, environment_variables)
        elif first_token == 'which':
            mycmd.whichsh(tokens, environment_variables, output)
        elif first_token == 'var':
            mycmd.varsh(tokens, environment_variables)
        else:
            seeker.run_command(tokens, environment_variables, output_fd)

        os.dup2(fd_cp, 0)
        if pipe:
            break

def main() -> None:
    # DO NOT REMOVE THIS FUNCTION CALL!
    setup_signals()

    # MYCODES HERE
    os.environ.update(setter.load_envars())
    if "PROMPT" not in os.environ.keys():
        os.environ.update({"PROMPT": ">> "})
    if "MYSH_VERSION" not in os.environ.keys():
        os.environ.update({"MYSH_VERSION": "1.0"})

    try:
        run_shell(os.environ)
    except EOFError:
        print()
    except KeyboardInterrupt:
        print()
        main()

if __name__ == "__main__":
    main()
