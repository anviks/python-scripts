import re

from .helpers import find_function_args


def replace_assert_that_call(m: re.Match) -> str:
    assert_that_args, start, end = find_function_args(m.string, m.end())

    if len(assert_that_args) > 1 and assert_that_args[1].startswith('Equals('):
        second = assert_that_args[1][7:-1].strip()
        # If the second argument contains operators with same or lower precedence than `==`, wrap it in parentheses
        if re.search(r'\||&|==|!=|\^', second):
            second = f'({second})'
        replacement = f'REQUIRE({assert_that_args[0].strip()} == {second})'
    elif len(assert_that_args) == 1:
        replacement = f'REQUIRE({assert_that_args[0].strip()})'
    else:
        raise ValueError(f'Unexpected arguments: {assert_that_args}')

    return m.string[:m.start()] + replacement + m.string[end + 1:]


def igloo_to_catch2(tests: str):
    tests = re.sub(r'#include <igloo/igloo\.h>\n', '', tests, count=1)
    tests = re.sub(r'using namespace igloo;\n', '', tests, count=1)
    
    while m := re.search(r'Assert::That', tests):
        tests = replace_assert_that_call(m)
    
    tests = re.sub(r'Describe ?\((\w+)\)', r'TEST_CASE("\1")', tests)
    tests = re.sub(r'It ?\((\w+)\)', r'SECTION("\1")', tests)

    return tests
