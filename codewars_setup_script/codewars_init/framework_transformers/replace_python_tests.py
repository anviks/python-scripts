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










###################

# Function to convert to snake_case
def to_snake_case(text):
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', '_', text)
    return text.lower()

# Regex pattern to find and transform the functions
def transform_code(code):
    describe_pattern = r'@test\.describe\("([^"]+)"\)\s+def\s+[a-zA-Z_][a-zA-Z0-9_]*\(\):'
    it_pattern = r'@test\.it\(\'([^\']+)\'\)\s+def\s+[a-zA-Z_][a-zA-Z0-9_]*\(\):'

    # Find the describe block
    describe_match = re.search(describe_pattern, code)
    if describe_match:
        describe_name = to_snake_case(describe_match.group(1))

        # Replace the `it` blocks inside the `describe` block
        def replace_it(match):
            it_name = to_snake_case(match.group(1))
            return f'def test_{describe_name}__{it_name}():'

        transformed_code = re.sub(it_pattern, replace_it, code)

        # Remove the original describe decorator
        transformed_code = re.sub(describe_pattern, '', transformed_code)
        return transformed_code.strip()

    return code



def codewars_test_to_pytest(tests: str):
    tests = tests.replace('import codewars_test as test', '')

    tests = transform_code(tests)
    
    return tests
    