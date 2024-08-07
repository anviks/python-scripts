import json
import os.path
import re
from typing import Any, TypedDict

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from .replace_python_tests import codewars_test_to_unittest

CURRENT_PATH = os.path.dirname(__file__)
LANG_TO_EXT = {
    'python': '.py',
    'typescript': '.ts',
    'javascript': '.js',
    'java': '.java',
    'kotlin': '.kt',
    'rust': '.rs',
    'cpp': '.cpp',
    'php': '.php',
}

PatternDict = TypedDict('PatternDict', {
    'class': dict[str, re.Pattern],
    'package': re.Pattern
})

PATTERNS: PatternDict = {
    'class': {
        'java': re.compile(r'(?:public +)?class +(\w+)'),
        'kotlin': re.compile(r'(?:public +)?(?:class|object) +(\w+)')
    },
    'package': re.compile(r'^package .*$', flags=re.MULTILINE)
}


def get_kata_path(difficulty: str, kata_title: str, language: str, file_contents: list[str]):
    difficulty = difficulty.lower()

    folder_prefix = '_' if difficulty.isdigit() and language in ('java', 'kotlin', 'rust') else ''
    folder_suffix = 'kyu' if difficulty.isdigit() else ''

    directory_structures = {
        'php': 'src/solutions/',
        'python': 'solutions/',
        'typescript': 'solutions/',
        'javascript': 'solutions/',
        'cpp': 'solutions/',
        'java': f'src/main/{language}/me/anviks/codewars/solutions/',
        'kotlin': f'src/main/{language}/me/anviks/codewars/solutions/',
        'rust': 'src/solutions/',
    }
    
    directory = directory_structures[language] + folder_prefix + difficulty + folder_suffix

    words: list[str] = re.findall(r'\w+', kata_title.lower())
    directory += '/' + '_'.join(words)

    if language in ('python', 'typescript', 'javascript', 'rust', 'cpp', 'php'):
        kata_file = 'solution_' + '_'.join(words)
        test_file = 'test_' + kata_file
    elif language in ('java', 'kotlin'):
        kata_class_match = PATTERNS['class'][language].search(file_contents[0])
        if not kata_class_match:
            kata_file = 'Solution'
        else:
            kata_file = kata_class_match.group(1)
        test_file = PATTERNS['class'][language].search(file_contents[1]).group(1)
    else:
        raise NotImplementedError('Not implemented for that language')

    return directory, kata_file, test_file


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


def fetch_kata_details(driver: Chrome, codewars_url: str, language: str) -> tuple[str, str, str, list[str]]:
    """
    Fetch the kata details including title, difficulty, and code snippets.
    """
    driver.get(f'{codewars_url}/train/{language}')
    WebDriverWait(driver, 10).until(lambda d: not d.find_element(By.TAG_NAME, 'h4').text.startswith('Loading '))

    kata_title_element = driver.find_element(By.TAG_NAME, 'h4')
    kata_title = kata_title_element.text
    difficulty_element = kata_title_element.find_element(By.XPATH, '../div/div/span')
    difficulty = difficulty_element.text.split(' ')[0]
    description_element = driver.find_element(By.ID, 'description')

    file_contents = [
        driver.execute_script("return arguments[0].CodeMirror.getValue()", container)
        for container in driver.find_elements(By.CLASS_NAME, 'CodeMirror')
    ]

    return kata_title, difficulty, description_element.get_attribute('innerHTML'), file_contents


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


def handle_existing_directory(directory: str, kata_file: str, test_file: str, language: str) -> tuple[str, str, str]:
    """
    Handle the scenario where the kata directory already exists.
    """
    if os.path.exists(directory):
        prompt = input(
            'Directory already exists for a kata with the same name. Would you like to overwrite, rename, or cancel? [o/r/c]\n')
        if prompt == 'c':
            return '', '', ''
        elif prompt == 'r':
            i = 1
            while os.path.exists(f'{directory}_{i}'):
                i += 1
            directory += f'_{i}'
            if language in ('python', 'typescript', 'javascript', 'cpp', 'php', 'rust'):
                kata_file += f'_{i}'
                test_file += f'_{i}'
            elif language in ('java', 'kotlin'):
                kata_file += f'{i}'
                test_file += f'{i}'
        elif prompt != 'o':
            raise ValueError('Invalid input')

    return directory, kata_file, test_file


def create_files(
        directory: str,
        kata_file: str,
        test_file: str,
        description: str,
        file_contents: list[str],
        language: str,
        format_vars: dict[str, Any]
):
    """
    Create the necessary files for the kata solution and tests.
    """
    kata_path = f'{directory}/{kata_file}{LANG_TO_EXT[language]}'
    test_path = f'{directory}/{test_file}{LANG_TO_EXT[language]}'
    description_path = f'{directory}/README.md'

    os.makedirs(directory, exist_ok=True)
    templates_dir = f'{CURRENT_PATH}/../templates/{language}'

    content, tests = file_contents

    if language in ('java', 'kotlin'):
        content = PATTERNS['package'].sub('', content)
        tests = PATTERNS['package'].sub('', tests)
        package_name = directory.replace(f'src/main/{language}/', '').replace('/', '.')
    elif language == 'python':
        with open(test_path[:-3] + '_original.py', 'w', encoding='utf-8') as f:
            f.write(tests)
        tests = codewars_test_to_unittest(tests)
        tests = '\n'.join(line for line in tests.splitlines() if
                          not line.startswith('from solution import') and not line.startswith('import solution'))

    format_vars.update(locals())

    with (open(f'{templates_dir}/solution', 'r', encoding='utf-8') as template, 
          open(kata_path, 'w', encoding='utf-8') as solution):
        solution.write(template.read().format_map(format_vars))

    with (open(f'{templates_dir}/tests', 'r', encoding='utf-8') as template, 
          open(test_path, 'w', encoding='utf-8') as tests_file):
        tests_file.write(template.read().format_map(format_vars))

    with open(description_path, 'w', encoding='utf-8') as desc_file:
        desc_file.write(description)


def main():
    codewars_url_input = input('Enter the url of a codewars kata you\'re about to solve:\n')
    codewars_url_match = re.search(r'(https://www\.codewars\.com/kata/[\w-]+)(?:/train/([a-z]+))?', codewars_url_input)
    if not codewars_url_match:
        raise ValueError('Invalid codewars url')

    codewars_url = codewars_url_match.group(1)
    language = codewars_url_match.group(2)

    history = load_history()

    previous_language = history['previousLanguage'] or 'python'
    language = language or input(f'Language? [{previous_language}]\n') or previous_language

    update_history(history, language, previous_language)

    driver = setup_driver(headless=True)
    kata_title, difficulty, description, file_contents = fetch_kata_details(driver, codewars_url, language)
    directory, kata_file, test_file = get_kata_path(difficulty, kata_title, language, file_contents)
    directory, kata_file, test_file = handle_existing_directory(directory, kata_file, test_file, language)

    if not directory:
        driver.quit()
        return

    create_files(directory, kata_file, test_file, description, file_contents, language, locals())

    driver.quit()


if __name__ == '__main__':
    main()
