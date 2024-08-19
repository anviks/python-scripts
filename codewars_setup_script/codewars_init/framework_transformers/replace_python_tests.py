import ast
import re
import types
from typing import AnyStr


####################################################################################################
#                                             UNITTEST                                             #
####################################################################################################


def _test_group_to_class(m: re.Match) -> str:
    groups = m.groupdict()
    tests_name: AnyStr = groups['test_group'].title()
    if groups['decorator']:
        class_name = ''.join(re.findall(r'[a-zA-Z0-9]+', tests_name))
    else:
        class_name = 'SolutionTests'
    return f'class {class_name}(unittest.TestCase):'


def _test_case_to_method(m: re.Match) -> str:
    groups = m.groupdict()
    test_case_name: AnyStr = groups['test_case'].lower()
    if groups['decorator']:
        function_name = '_'.join(re.findall(r'\w+', test_case_name))
    else:
        function_name = 'solution'
    return f'    def test_{function_name}(self):'


def _handle_ungrouped_tests(m: re.Match) -> str:
    indented = '\n'.join(' ' * 8 + line for line in m.group().splitlines())
    return 'class SolutionTests(unittest.TestCase):\n    def test_solution(self):\n' + indented


def _function_to_method(m: re.Match) -> str:
    if m.group(2):
        return m.group(1) + 'self, ' + m.group(2)
    else:
        return m.group(1) + 'self'


def codewars_test_to_unittest(tests: str):
    tests = tests.replace('import codewars_test as test', 'import unittest').replace('test.assert_equals', 'self.assertEqual')
    tests = re.sub(r'(?P<decorator>@)?test\.describe\((?P<quote>["\'])(?P<test_group>.+?)(?P=quote)\)(?(decorator)\ndef \w+\(\):)', _test_group_to_class, tests)
    tests = re.sub(r'[ \t]*(?P<decorator>@)?test\.it\((?P<quote>["\'])(?P<test_case>.+?)(?P=quote)\)(?(decorator)\n[ \t]*?def \w+\(\):)', _test_case_to_method, tests)
    tests = re.sub(r'(?:^self\..+\n?)+', _handle_ungrouped_tests, tests, flags=re.MULTILINE)
    tests = re.sub(r'( {4}def (?!test_)\w+\()(\w)?', _function_to_method, tests)
    methods = re.findall(r'(?!.*#) {4}def (?!test_)(\w+)\(self', tests)
    
    for method in methods:
        tests = re.sub(fr'^(?!.*def )(?!.*#)(.*){method}', fr'\1self.{method}', tests, flags=re.MULTILINE)
        
    return tests


####################################################################################################
#                                              PYTEST                                              #
####################################################################################################

def replace_test_functions(tests: str):
    lines = tests.splitlines()
    result_lines = []
    test_func_name = ''
    extra_indentation = ''
    i = 0

    while i < len(lines):
        line = lines[i]

        if m := re.search(r'(?P<decorator>@)?test\.describe\((?P<quote>["\'])(?P<test_group>.+?)(?P=quote)\)', line):
            groups = m.groupdict()

            if groups['decorator']:
                i += 1  # Skip function declaration
            else:
                extra_indentation = 4 * ' '

            test_func_name = '_'.join(re.findall(r'\w+', m['test_group'].lower()))

        elif m := re.search(r'(?P<decorator>@)?test\.it\((?P<quote>["\'])(?P<test_case>.+?)(?P=quote)\)', line):
            groups = m.groupdict()

            if groups['decorator']:
                i += 1  # Skip function declaration
            else:
                extra_indentation = 4 * ' '

            test_case_name = '_'.join(re.findall(r'\w+', m['test_case'].lower()))

            if test_func_name:
                test_func_name = test_func_name.split('__')[0] + '__' + test_case_name
            else:
                test_func_name = test_case_name

        elif test_func_name and line.strip() and not line.strip().startswith('#') or 'test.assert_equals' in line:
            if not test_func_name and line.startswith('test.assert_equals'):
                test_func_name = 'example'
                result_lines.append('def test_' + test_func_name + '():')
                extra_indentation += ' ' * 4
            elif test_func_name and 'def test_' + test_func_name + '():' not in result_lines:
                result_lines.append('def test_' + test_func_name + '():')

            result_lines.append(extra_indentation + line)

        else:
            result_lines.append(extra_indentation + line)

        i += 1

    return '\n'.join(result_lines)


def _replace_assert_equals_call(tests: str):
    tree = ast.parse(tests)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue

        func = node.value.func
        args = node.value.args

        if not isinstance(func, ast.Attribute) or func.value.id != 'test':
            continue

        if func.attr == 'assert_equals':
            if isinstance(args[1], ast.Constant):
                op = ast.Is() if type(args[1].value) in [bool, types.NoneType] else ast.Eq()
            else:
                op = ast.Eq()
            node.value = ast.Assert(msg=None, test=ast.Compare(left=args[0], ops=[op], comparators=[args[1]]))

            if len(args) == 3:
                node.value.msg = args[2]

    return ast.unparse(tree)


def codewars_test_to_pytest(tests: str):
    tests = tests.replace('import codewars_test as test', '')
    tests = replace_test_functions(tests)
    tests = _replace_assert_equals_call(tests)

    return tests.replace('\n    \n    ', '\n    ')
