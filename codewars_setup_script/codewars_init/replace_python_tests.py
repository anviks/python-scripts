import re
from typing import AnyStr


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