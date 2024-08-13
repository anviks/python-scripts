from . import LanguageHandler


class PhpHandler(LanguageHandler):
    def get_extension(self) -> str:
        return 'php'
    
    def get_directory(self) -> str:
        return 'src/solutions/'
