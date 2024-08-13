from typing import Any

from . import LanguageHandler, SourceFile
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

    def get_files_to_create(self, kata_slug: str, files: list[SourceFile]) -> list[SourceFile]:
        return [
            SourceFile(f'solution_{kata_slug}', self.get_extension(), 'solution', files[0].contents),
            SourceFile(f'test_{kata_slug}', self.get_extension(), 'test', files[1].contents),
            SourceFile(f'solution_{kata_slug}', 'hpp', 'header')
        ]

    def get_directory(self) -> str:
        return 'solutions/'

    def edit_file_contents(self, files: list[SourceFile]) -> None:
        files[1].contents = igloo_to_catch2(files[1].contents)
    
