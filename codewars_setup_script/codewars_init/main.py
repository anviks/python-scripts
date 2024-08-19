import json
import os.path
import re
import sys
from typing import Any

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from requests import get

from .framework_transformers.helpers import parse_conditional_rendering
from .language_handlers import CHandler, CppHandler, JavaHandler, JavascriptHandler, KotlinHandler, LanguageHandler, \
    PhpHandler, PythonHandler, RustHandler, TypescriptHandler, SourceFile

CURRENT_PATH = os.path.dirname(__file__)
TEMPLATES_DIR = f'{CURRENT_PATH}/../templates'


class LanguageFactory:
    handlers = {
        'c': CHandler,
        'cpp': CppHandler,
        'java': JavaHandler,
        'javascript': JavascriptHandler,
        'kotlin': KotlinHandler,
        'php': PhpHandler,
        'python': PythonHandler,
        'rust': RustHandler,
        'typescript': TypescriptHandler,
    }

    @staticmethod
    def get_handler(language: str) -> LanguageHandler:
        if language not in LanguageFactory.handlers:
            raise NotImplementedError(f'Handler not implemented for language: {language}')
        return LanguageFactory.handlers[language]()


def get_difficulty_directory(difficulty: int | None, handler: LanguageHandler) -> str:
    directory = handler.get_directory()
    
    if difficulty is not None:
        directory += f'{handler.get_numeric_folder_prefix()}{-difficulty}kyu'
    else:
        directory += 'unreleased'

    return directory


def setup_driver(*, headless: bool) -> Chrome:
    """
    Set up the Chrome WebDriver with headless options.
    """
    options = Options()
    if headless:
        options.add_argument('--headless')
    driver = Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


def fetch_kata_details(driver: Chrome, codewars_url: str, language: str) -> tuple[str, str, int | None, str, list[SourceFile]]:
    """
    Fetch the kata details including title, difficulty, and code snippets.
    """
    driver.get(f'{codewars_url}/train/{language}')
    WebDriverWait(driver, 10).until(lambda d: not d.find_element(By.TAG_NAME, 'h4').text.startswith('Loading '))

    kata_id = codewars_url.split('/')[-1]
    response = get('https://www.codewars.com/api/v1/code-challenges/' + kata_id).json()
    kata_title = response['name']
    slug = response['slug'].replace('-', '_')
    difficulty = response['rank']['id']
    description = parse_conditional_rendering(response['description'], language)
    description = f'# [{kata_title}]({codewars_url})\n\n{description}'

    files = [
        SourceFile(contents=driver.execute_script("return arguments[0].CodeMirror.getValue()", container))
        for container in driver.find_elements(By.CLASS_NAME, 'CodeMirror')
    ]

    return kata_title, slug, difficulty, description, files


def load_history() -> dict:
    """
    Load the history from the history.json file.
    """
    with open(f'{CURRENT_PATH}/../history.json') as f:
        return json.load(f)


def save_history(history: dict):
    """
    Save the updated history to the history.json file.
    """
    with open(f'{CURRENT_PATH}/../history.json', 'w') as f:
        json.dump(history, f)


def update_history(history: dict, language: str, previous_language: str):
    """
    Update the language history if it has changed.
    """
    if language != previous_language:
        history['previousLanguage'] = language
        save_history(history)


def handle_existing_directory(directory: str, files: list[SourceFile], handler: LanguageHandler) -> tuple[str, list[SourceFile]]:
    """
    Handle the scenario where the kata directory already exists.
    """
    if os.path.exists(directory):
        prompt = input(
            'Directory already exists for a kata with the same name. Would you like to overwrite, rename, or cancel? [o/r/c]\n')
        if prompt == 'c':
            return '', []
        elif prompt == 'r':
            i = 1
            while os.path.exists(f'{directory}_{i}'):
                i += 1
            directory += f'_{i}'
            for file in files:
                file.name += handler.get_duplicate_suffix(i)
        elif prompt != 'o':
            raise ValueError('Invalid input')

    return directory, files


def create_files(
        directory: str,
        files: list[SourceFile],
        description: str,
        language: str,
        format_vars: dict[str, Any]
):
    """
    Create the necessary files for the kata solution and tests.
    """
    os.makedirs(directory, exist_ok=True)
    
    for file in files:
        with (open(f'{TEMPLATES_DIR}/{language}/{file.template_name}', 'r', encoding='utf-8') as template, 
              open(f'{directory}/{file.name}.{file.extension}', 'w', encoding='utf-8') as kata_file):
            kata_file.write(template.read().format_map(format_vars))

    with open(f'{directory}/README.md', 'w', encoding='utf-8') as desc_file:
        desc_file.write(description)


def main():
    if len(sys.argv) > 1:
        codewars_url_input = sys.argv[1]
    else:
        codewars_url_input = input('Enter the url of a codewars kata you\'re about to solve:\n')
    
    codewars_url_match = re.search(r'(https://www\.codewars\.com/kata/[\w-]+)(?:(?:/train)?/([a-z]+))?', codewars_url_input)
    if not codewars_url_match:
        raise ValueError('Invalid codewars url')

    codewars_url = codewars_url_match.group(1)
    language = codewars_url_match.group(2)

    history = load_history()
    previous_language = history['previousLanguage'] or 'python'
    language = language or input(f'Language? [{previous_language}]\n') or previous_language
    
    handler = LanguageFactory.get_handler(language)

    update_history(history, language, previous_language)

    driver = setup_driver(headless=True)
    kata_title, kata_slug, difficulty, description, files = fetch_kata_details(driver, codewars_url, language)
    kata_directory = get_difficulty_directory(difficulty, handler) + '/' + kata_slug

    files = handler.get_files_to_create(kata_slug, files)
    kata_directory, files = handle_existing_directory(kata_directory, files, handler)

    if not kata_directory:
        driver.quit()
        return

    handler.edit_file_contents(files)
    format_vars = handler.get_format_args(files, kata_directory, codewars_url)
    create_files(kata_directory, files, description, language, format_vars)

    driver.quit()


if __name__ == '__main__':
    main()
