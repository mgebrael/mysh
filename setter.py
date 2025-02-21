"""
Module for initialising and substituting shell variables.
"""
import json
import sys
import os
import re

def load_envars() -> dict:
    '''
    Load environment variables from .myshrc.
    '''
    try:
        if "MYSHDOTDIR" in os.environ.keys():
            mysh_json = open(os.environ["MYSHDOTDIR"] + "/.myshrc")
        else:
            mysh_json = open("./.myshrc")
        environment_variables = json.load(mysh_json)
        mysh_json.close()

        # if "PROMPT" not in environment_variables.keys():
        #     environment_variables["PROMPT"] = ">> "

        for variable, value in environment_variables.items():
            if isinstance(value, int):
                print(f"mysh: .myshrc: {variable}: not a string", file=sys.stderr)
                return {}
            if re.search("[^A-Za-z0-9_]", variable) is not None:
                print(f"mysh: .myshrc: {variable}: invalid characters for variable name",
                      file=sys.stderr)
                return {}

        return environment_variables

    except FileNotFoundError:
        return {}

    except json.decoder.JSONDecodeError:
        print("mysh: invalid JSON format for .myshrc", file=sys.stderr)
        mysh_json.close()
        return {}

def substitute_variables(line: str, environment_variables: dict[str, str]) -> str | None:
    '''
    Substitutes variable names with their values.
    '''
    while True:
        # searches valid and invalid uses of variable syntax
        var_search = re.search(r"^\${[A-Za-z0-9_]*}|[^\\]\${[A-Za-z0-9_]*}", line)
        invalid_var_search = re.search(r"^\${[^ ]+}|[^\\]\${[^ ]+}", line)

        if var_search != None:
            start, end = var_search.span()
            if line[start] != "$":
                start += 1

            var_name = line[start:end][2:-1]

            if var_name == '':
                line = line[:start] + line[end:]
                continue

            try:
                line = line[:start] + environment_variables[var_name] + line[end:]
            except KeyError:
                line = line[:start] + line[end:]

            continue

        if invalid_var_search != None:
            start, end = invalid_var_search.span()
            if line[start] != "$":
                start += 1

            invalid_var = line[start:end][2:-1]
            print("mysh: syntax error: invalid characters for variable", invalid_var,
                  file=sys.stderr)
            return

        break

    line = re.sub(r"\\\$", "$", line)
    return line
