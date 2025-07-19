import re
from typing import Any

from . import LanguageHandler, SourceFile
from ..data_transfer import KataDetails


class JavaHandler(LanguageHandler):
    def get_format_args(self, files: list[SourceFile], directory: str, codewars_url: str) -> dict[str, Any]:
        return {
            'codewars_url': codewars_url,
            'package_name': directory.replace('src/main/java/', '').replace('/', '.'),
            'solution': files[0].contents,
            'tests': files[1].contents
        }

    def get_extension(self) -> str:
        return 'java'

    def get_directory(self) -> str:
        return 'src/main/java/me/anviks/codewars/solutions/'

    def get_files_to_create(self, kata_slug: str, file_contents: list[str]) -> list[SourceFile]:
        class_pattern = re.compile(r'(?:public +)?class +(\w+)')

        kata_class_match = class_pattern.search(file_contents[0])
        solution_file_name = kata_class_match.group(1)
        test_file_name = class_pattern.search(file_contents[1]).group(1)

        return [
            SourceFile(solution_file_name, self.get_extension(), 'solution', file_contents[0]),
            SourceFile(test_file_name, self.get_extension(), 'test', file_contents[1])
        ]

    def edit_file_contents(self, details: KataDetails, kata_directory: str) -> None:
        for file in files:
            file.contents = '\n'.join(line for line in file.contents.splitlines()
                                      if not line.startswith('package '))

    def get_numeric_folder_prefix(self):
        return '_'

    def get_duplicate_suffix(self, number: int):
        return str(number)
