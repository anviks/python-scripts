from typing import Any

from . import LanguageHandler, SourceFile


class CHandler(LanguageHandler):
    def get_format_args(self, files: list[SourceFile], directory: str, codewars_url: str) -> dict[str, Any]:
        return {
            'codewars_url': codewars_url,
            'solution_file_name': files[0].name,
            'solution_file_name_upper': files[0].name.upper(),
            'solution': files[0].contents,
            'tests': files[1].contents
        }

    def get_extension(self) -> str:
        return 'c'

    def get_files_to_create(self, kata_slug: str, files: list[SourceFile]) -> list[SourceFile]:
        return [
            SourceFile(f'solution_{kata_slug}', self.get_extension(), 'solution', files[0].contents),
            SourceFile(f'test_{kata_slug}', self.get_extension(), 'test', files[1].contents),
            SourceFile(f'solution_{kata_slug}', 'h', 'header')
        ]

    def get_directory(self) -> str:
        return 'src/solutions/'
