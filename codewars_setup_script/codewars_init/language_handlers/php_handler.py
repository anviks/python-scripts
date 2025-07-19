import re

from . import LanguageHandler, SourceFile


class PhpHandler(LanguageHandler):
    def get_extension(self) -> str:
        return 'php'
    
    def get_directory(self) -> str:
        return 'src/solutions/'

    def get_files_to_create(self, kata_slug: str, file_contents: list[str]) -> list[SourceFile]:
        class_name = kata_slug.title().replace('_', '') + 'Test'
        file_contents[1] = re.sub(r'(?<=class )\w+(?=\s*extends TestCase)', class_name, file_contents[1])
        
        return [
            SourceFile(f'solution_{kata_slug}', self.get_extension(), 'solution', file_contents[0]),
            SourceFile(class_name, self.get_extension(), 'test', file_contents[1])
        ]
