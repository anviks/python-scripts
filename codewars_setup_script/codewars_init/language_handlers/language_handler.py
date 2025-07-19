from abc import ABC, abstractmethod
from typing import Any

from ..data_transfer import SourceFile


class LanguageHandler(ABC):
    @abstractmethod
    def get_extension(self) -> str:
        pass

    @abstractmethod
    def get_directory(self) -> str:
        pass

    def get_format_args(self, files: list[SourceFile], directory: str, codewars_url: str) -> dict[str, Any]:
        return {
            'codewars_url': codewars_url,
            'solution_file_name': files[0].name,
            'solution': files[0].contents,
            'tests': files[1].contents
        }

    def get_files_to_create(self, kata_slug: str, file_contents: list[str]) -> list[SourceFile]:
        """
        Return a list of tuples with file names (without extension) and their template names.
        """
        return [
            SourceFile(f'solution_{kata_slug}', self.get_extension(), 'solution', file_contents[0]),
            SourceFile(f'test_{kata_slug}', self.get_extension(), 'test', file_contents[1])
        ]

    def get_numeric_folder_prefix(self):
        return ''

    def get_duplicate_suffix(self, number: int):
        return f'_{number}'

    def edit_file_contents(self, files: list[SourceFile], kata_directory: str) -> None:
        pass
