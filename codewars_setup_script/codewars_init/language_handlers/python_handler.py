from . import LanguageHandler, SourceFile
from ..data_transfer import KataDetails
from ..framework_transformers.replace_python_tests import codewars_test_to_pytest


class PythonHandler(LanguageHandler):
    def get_extension(self) -> str:
        return 'py'

    def get_directory(self) -> str:
        return 'src/solutions/'

    def get_files_to_create(self, kata_slug: str, file_contents: list[str]) -> list[SourceFile]:
        """
        Return a list of tuples with file names (without extension) and their template names.
        """
        return [
            SourceFile(f'solution_{kata_slug}', self.get_extension(), 'solution', file_contents[0]),
            SourceFile(f'test_{kata_slug}', self.get_extension(), 'test', file_contents[1]),
        ]

    def edit_file_contents(self, details: KataDetails, kata_directory: str) -> None:
        details.files[1].contents = codewars_test_to_pytest(details.files[1].contents)
        details.files[1].contents = '\n'.join(line for line in details.files[1].contents.splitlines()
                                      if not line.startswith('from solution import')
                                      and not line.startswith('import solution'))
