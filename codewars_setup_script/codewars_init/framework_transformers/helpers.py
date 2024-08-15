import re


def find_function_args(string: str, starting_index: int) -> tuple[list[str], int | None, int]:
    """
    Given a string of code, find the arguments of a function call starting at the given index.
    
    For example, given the string:
        
        ```
        foo(1, 2, 3)
        bar(4, (5, 6), 7)
        ```
    
    If the starting index is 0, the function will return `['1', '2', '3']`.
    If the starting index is 15 (the index of the `b` in `bar`), the function will return `['4', '(5, 6)', '7']`.
    
    Note: Argument search will start after the first occurrence of `(` after or at the starting index 
    and will end at the matching `)` of the first `(` found.
    :param string: The string of code to search.
    :param starting_index: The index to start searching from.
    :return: A list of strings representing the arguments of the function call.
    """
    start_pos = arg_start = None
    stack = 0
    args = []

    for i in range(starting_index, len(string)):
        char = string[i]
        if char == '(':
            if stack == 0:
                start_pos = arg_start = i + 1

            stack += 1
        elif char == ')':
            stack -= 1

            if stack == 0:
                args.append(string[arg_start:i].strip())
                return args, start_pos, i

        if stack == 1 and char == ',':
            args.append(string[arg_start:i].strip())
            arg_start = i + 1

    return args, start_pos, len(string)


def parse_conditional_rendering(text, active_language):
    pattern_remove_ifs = re.compile(fr'(?P<backticks>`{{3,}}|~{{3}})if:(?:(?!{active_language}).)*?\n.+?\n(?P=backticks)\n+', flags=re.DOTALL)
    pattern_remove_if_nots = re.compile(fr'(?P<backticks>`{{3,}}|~{{3}})if-not:[^\n]*?(?={active_language})[^\n]+?\n.+?\n(?P=backticks)\n+', flags=re.DOTALL)
    pattern_unwrap_ifs_and_if_nots = re.compile(r'(?P<backticks>`{3,}|~{3})if[^\n]+\n(?P<content>.+?)\n(?P=backticks)', flags=re.DOTALL)
    pattern_remove_code_blocks = re.compile(fr'(?P<backticks>`{{3,}}|~{{3}})(?!{active_language}|if)[^\n]+\n.+?\n(?P=backticks)\n+', flags=re.DOTALL)
    
    text = pattern_remove_ifs.sub('', text)
    text = pattern_remove_if_nots.sub('', text)
    text = pattern_unwrap_ifs_and_if_nots.sub(r'\g<content>', text)
    text = pattern_remove_code_blocks.sub('', text)

    return text
