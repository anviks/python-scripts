import re

from . import LanguageHandler, SourceFile


class PhpHandler(LanguageHandler):
    def get_extension(self) -> str:
        return 'php'
    
    def get_directory(self) -> str:
        return 'src/solutions/'

    def get_files_to_create(self, kata_slug: str, files: list[SourceFile]) -> list[SourceFile]:
        class_name = kata_slug.title().replace('_', '') + 'Test'
        files[1].contents = re.sub(r'(?<=class )\w+(?=\s*extends TestCase)', class_name, files[1].contents)
        
        return [
            SourceFile(f'solution_{kata_slug}', self.get_extension(), 'solution', files[0].contents),
            SourceFile(class_name, self.get_extension(), 'test', files[1].contents)
        ]
