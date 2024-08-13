import re
from typing import Any

from . import LanguageHandler, SourceFile


class KotlinHandler(LanguageHandler):
    def get_format_args(self, files: list[SourceFile], directory: str, codewars_url: str) -> dict[str, Any]:
        return {
            'codewars_url': codewars_url,
            'package_name': directory.replace('src/main/java/', '').replace('/', '.'),
            'solution': files[0].contents,
            'tests': files[1].contents
        }
    
    def get_extension(self) -> str:
        return 'kt'

    def get_directory(self) -> str:
        return 'src/main/kotlin/me/anviks/codewars/solutions/'

    def get_files_to_create(self, kata_slug: str, files: list[SourceFile]) -> list[SourceFile]:
        class_pattern = re.compile(r'(?:public +)?(?:class|object) +(\w+)')
        kata_class_match = class_pattern.search(files[0].contents)

        if not kata_class_match:
            solution_file_name = 'Solution'
        else:
            solution_file_name = kata_class_match.group(1)
        test_file_name = class_pattern.search(files[1].contents).group(1)
        
        return [
            SourceFile(solution_file_name, self.get_extension(), 'solution', files[0].contents),
            SourceFile(test_file_name, self.get_extension(), 'test', files[1].contents)
        ]

    def edit_file_contents(self, files: list[SourceFile]) -> None:
        for file in files:
            file.contents = '\n'.join(line for line in file.contents.splitlines()
                                      if not line.startswith('package '))

    def get_numeric_folder_prefix(self):
        return '_'

    def get_duplicate_suffix(self, number: int):
        return str(number)
