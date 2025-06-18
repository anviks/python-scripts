import re


def criterion_to_catch2(tests: str):
    # Convert Test to TEST_CASE
    # Test(math, add_test) -> TEST_CASE("math:add_test", "[math]")
    def convert_test_case(match):
        suite_name = match.group(1)
        test_name = match.group(2)
        return f'TEST_CASE("{suite_name}:{test_name}", "[{suite_name}]")'

    catch2_code = re.sub(r'\bTest\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)', convert_test_case, tests)

    # Convert cr_assert to REQUIRE
    # cr_assert(condition) -> REQUIRE(condition)
    catch2_code = re.sub(r'\bcr_assert\s*\(\s*(.*?)\s*\)', r'REQUIRE(\1)', catch2_code)

    # Convert cr_assert_not to REQUIRE
    # cr_assert_not(condition) -> REQUIRE(!condition)
    catch2_code = re.sub(r'\bcr_assert_not\s*\(\s*(.*?)\s*\)', r'REQUIRE_FALSE(\1)', catch2_code)

    # Convert cr_expect to CHECK
    # cr_expect(condition) -> CHECK(condition)
    catch2_code = re.sub(r'\bcr_expect\s*\(\s*(.*?)\s*\)', r'CHECK(\1);', catch2_code)
    
    # Convert cr_expect_not to CHECK
    # cr_expect_not(condition) -> CHECK(!condition)
    catch2_code = re.sub(r'\bcr_expect_not\s*\(\s*(.*?)\s*\)', r'CHECK(!\1);', catch2_code)
    
    # Place error message argument to a correct place
    # REQUIRE(condition, "error message") -> REQUIRE(condition) << "error message"
    catch2_code = re.sub(r'((?:REQUIRE|CHECK)(?:_FALSE)?)(?=\(.+?,\s*"(?:[^"\\]|\\.)*"\);)', r'\1_MSG', catch2_code)

    # Convert include from criterion to catch2
    # #include <criterion/criterion.h> -> #include <catch2/catch.hpp>
    catch2_code = re.sub(r'#include\s*<criterion/criterion.h>', '', catch2_code)

    return catch2_code
