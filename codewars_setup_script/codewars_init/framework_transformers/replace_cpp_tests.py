import re


def igloo_to_catch2(tests: str):
    tests = '#include <catch2/catch_all.hpp>\n' + tests
    tests = re.sub(r'#include <igloo/igloo\.h>\n', '', tests, count=1)
    tests = re.sub(r'using namespace igloo;\n', '', tests, count=1)
    tests = re.sub(r'Assert::That\((.+?), Equals\((.+?)\)\)', r'REQUIRE(\1 == \2)', tests, flags=re.DOTALL)
    tests = re.sub(r'Describe ?\((\w+)\)', r'TEST_CASE("\1")', tests)
    tests = re.sub(r'It ?\((\w+)\)', r'SECTION("\1")', tests)
    
    return tests
