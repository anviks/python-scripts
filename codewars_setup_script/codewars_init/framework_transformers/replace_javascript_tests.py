import re


def codewars_test_to_chai(tests: str):
    tests = re.sub(
        r'^.*?(?=(?P<var>\w+) = ?require\((?P<quote>["\'])@codewars/test-compat(?P=quote)).*$',
        """\
import { assert } from 'chai';
const \\g<var> = {
assertSimilar: assert.deepEqual,
assertEquals: assert.strictEqual,
assertDeepEquals: assert.deepEqual,
expect: assert.isTrue,
expectError: (message, fn) => assert.throws(fn, null, null, message),
};\
""",
        tests,
        flags=re.MULTILINE
    )

    tests = re.sub(
        r'^.*? ?{ ?assert ?} ?= ?require\((?P<quote>["\'])chai(?P=quote).*$',
        'import { assert } from \'chai\';',
        tests,
        flags=re.MULTILINE)
    
    return tests