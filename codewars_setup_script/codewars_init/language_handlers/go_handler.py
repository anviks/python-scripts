import re
from . import LanguageHandler, SourceFile
from ..data_transfer import KataDetails


class GoHandler(LanguageHandler):
    IMPORTS_REPLACEMENT = """
import (
    . "codewarsGo/{directory}"
    "testing"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func Test{pascal_case_slug}(t *testing.T) {{
    RegisterFailHandler(Fail)
    RunSpecs(t, "{pascal_case_slug} Suite")
}}
"""

    def get_extension(self) -> str:
        return 'go'

    def get_directory(self) -> str:
        return 'src/solutions/'

    def get_files_to_create(self, kata_slug: str, file_contents: list[str]) -> list[SourceFile]:
        return [
            SourceFile(f'{kata_slug}_solution', self.get_extension(), 'solution', file_contents[0]),
            SourceFile(f'{kata_slug}_test', self.get_extension(), 'test', file_contents[1]),
        ]

    def edit_file_contents(self, details: KataDetails, kata_directory: str) -> None:
        pascal_case_slug = details.slug.replace('_', ' ').title().replace(' ', '')

        tests_file = details.files[1].contents
        tests_file = re.sub(
            r'import \(.*?\)',
            self.IMPORTS_REPLACEMENT.format(directory=kata_directory, pascal_case_slug=pascal_case_slug),
            tests_file,
            flags=re.DOTALL
        )
        details.files[1].contents = tests_file
