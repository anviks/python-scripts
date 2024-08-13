from . import LanguageHandler, SourceFile
from ..framework_transformers.replace_javascript_tests import codewars_test_to_chai


class TypescriptHandler(LanguageHandler):
    def get_extension(self) -> str:
        return 'ts'
    
    def get_directory(self) -> str:
        return 'src/solutions/'

    def edit_file_contents(self, files: list[SourceFile]) -> None:
        files[1].contents = codewars_test_to_chai(files[1].contents)
