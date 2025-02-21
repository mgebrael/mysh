# Report

## Executing Commands From Lines of Input

When a user enters a line of input into the shell, it is first split into arguments using
the `shlex` module:

```python
# shlex analyzer for splitting a line into arguments
analyzer = shlex.shlex(line, posix=True)
analyzer.escapedquotes = '"\''
analyzer.whitespace_split = True
```

The shlex instance `analyzer` is set to read characters from the provided `line` under the
POSIX set of standards followed by mysh, apart from the following minor changes:

- In addition to `"`, `'` is also accepted as a valid escape character when in quotes.
- Tokens are limited to split only on whitespace characters.

Then, the tokens are interpreted by the following checks:

- If there are no tokens (the line of input was empty), continue and display a new prompt.
- Otherwise, if the first token is one of the built-in commands (exit, pwd, cd, which, var)
call the respective function from `mycmd.py`, passing in all tokens and other relevant
arguments.
- Else, call `seeker.run_command()` and attempt to run the specified commmand corresponding
to an executable found on the `PATH`.

## Substituting Environment Variables

The logic for substituting variables occurs before user input is split into tokens, and is
handled by the `substitute_variables` function in `setter.py`.

In this function, occurrences of the shell variable syntax `${variable_name}` are located by
using regular expression via the `re` module. Initially two variables are set:

```python
# searches valid and invalid uses of variable syntax
var_search = re.search(r"^\${[A-Za-z0-9_]*}|[^\\]\${[A-Za-z0-9_]*}", line)
invalid_var_search = re.search(r"^\${[^ ]+}|[^\\]\${[^ ]+}", line)
```

The logic for both regular expressions are as follows:

- `|` splits the expression into two alternate cases:
    - First alternative: `^` finds the pattern at the start of a line.
    - Second alternative: `[^\\]` finds the pattern preceded by a character that is not a backslash.
- `\$`, `{` and `}` match literally with the characters `$`, `{` and `}`.

For `var_search`:

- `[A-Za-z0-9_]*` matches zero or more alphanumeric or underscore characters.

For `invalid_var_search`:

- `[^ ]+` matches one or more non-whitespace characters.

The `line` is searched for these patterns inside of a while loop that breaks when neither can
be found. If a valid variable usage is found, the function attempts to replace the line segment
with `environment_variables[var_name]`. If at some point there are no more valid variables in the
line, but there exists a match to the `invalid_var_search` variable, it is handled as an invalid
character error and the function returns early.

Once completed, all backslashed shell variables that have been ignored are substituted by
`line = re.sub(r"\\\$", "$", line)` so that they can be interpreted as literal strings.

## Pipelines

The process for handling pipelines is mainly contained within the piping section of `run_shell()`:

```python
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
```

If no pipeline is given, then `line` remains unchanged and the rest of the function is run
normally. However, if `split_by_pipe` contains more than one command, then procedurally pop
off and execute each command by using a while loop.

To redirect the `stdout` of one command to be read as the `stdin` of the next, the functions
`os.pipe` and `os.dup2`/`os.dup` are used.

- Firstly, `os.pipe()` returns two new file descriptors `fd_read, fd_write` used for capturing
the output of the current command.
- Calling itself, the command `pipe_segment` is passed as a line of input into `run_shell()`,
alongside the file descriptor `fd_write` to write in as well as the boolean condition `pipe`,
which ensures that the shell closes after executing the pipe segment.
- At the end, `fd_read` is duplicated to 0 (`stdin`) so that the next command that is
executed will read from the previous command's output rather than from user input.

Once the pipeline has ended, `stdin` is returned to normal by duplicating the copied `fd_cp`
back to 0.

## Tests

Tests created for mysh are organised under folders in the `tests/` directory. Each test folder
contains an .in file used for input, .out for intended output, .expected for expected error
messages, actual.txt for actual standard output and errors.txt for actual standard error.

In total, there are 23 unit tests and 3 end-to-end test cases. To run all tests, use
`bash tests/run_tests.sh` in the home directory.
