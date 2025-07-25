from typing import Any

from . import LanguageHandler, SourceFile
from ..data_transfer import KataDetails
from ..framework_transformers.replace_cpp_tests import igloo_to_catch2


class CppHandler(LanguageHandler):
    def get_format_args(self, files: list[SourceFile], directory: str, codewars_url: str) -> dict[str, Any]:
        return {
            'codewars_url': codewars_url,
            'solution_file_name': files[0].name,
            'solution_file_name_upper': files[0].name.upper(),
            'solution': files[0].contents,
            'tests': files[1].contents
        }

    def get_extension(self) -> str:
        return 'cpp'

    def get_files_to_create(self, kata_slug: str, file_contents: list[str]) -> list[SourceFile]:
        return [
            SourceFile(f'solution_{kata_slug}', self.get_extension(), 'solution', file_contents[0]),
            SourceFile(f'test_{kata_slug}', self.get_extension(), 'test', file_contents[1].contents),
            SourceFile(f'solution_{kata_slug}', 'hpp', 'header')
        ]

    def get_directory(self) -> str:
        return 'src/solutions/'

    def edit_file_contents(self, details: KataDetails, kata_directory: str) -> None:
        details.files[1].contents = igloo_to_catch2(details.files[1].contents)
