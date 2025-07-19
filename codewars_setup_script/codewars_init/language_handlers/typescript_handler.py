import re

from . import LanguageHandler
from ..data_transfer import KataDetails
from ..framework_transformers.replace_javascript_tests import codewars_test_to_chai


class TypescriptHandler(LanguageHandler):
    def get_extension(self) -> str:
        return 'ts'

    def get_directory(self) -> str:
        return 'src/solutions/'

    def edit_file_contents(self, details: KataDetails, kata_directory: str) -> None:
        details.files[1].contents = codewars_test_to_chai(details.files[1].contents)
        details.files[1].contents = '\n'.join(line for line in details.files[1].contents.splitlines()
                                      if not re.match(r'import \{.*} from ([\'"])(?:\./)?solution\1', line))
