from . import LanguageHandler, SourceFile


class RustHandler(LanguageHandler):
    def get_extension(self) -> str:
        return 'rs'
    
    def get_directory(self) -> str:
        return 'src/solutions/'
    
    def get_files_to_create(self, kata_slug: str, files: list[SourceFile]) -> list[SourceFile]:
        """
        Return a list of tuples with file names (without extension) and their template names.
        """
        return [
            SourceFile(f'solution_{kata_slug}', self.get_extension(), 'solution', files[0].contents),
            SourceFile(f'test_{kata_slug}', self.get_extension(), 'test', files[1].contents),
            SourceFile('mod', self.get_extension(), 'mod', '')
        ]

    def get_numeric_folder_prefix(self):
        return '_'