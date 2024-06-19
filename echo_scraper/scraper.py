import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime as dt
from types import TracebackType
from typing import Any, Self
from urllib.parse import urlparse

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from config_wrapper import EchoConfig
from domain import Echo360Lecture, FileInfo

logger = logging.getLogger(__name__)


class EchoScraper:
    def __init__(self,
                 configuration: EchoConfig,
                 course_title: str,
                 lecture_indices: slice,
                 *,
                 headless: bool = True):
        self.config = configuration
        self.course_title = course_title
        self.lecture_indices = lecture_indices
        self.headless = headless

        self.lectures: list[Echo360Lecture] = []
        self.__driver: WebDriver | None = None
        self.course_url = self.config.course_urls[self.course_title]
        self.searched_files = self.config.searched_files[self.course_title]

    @property
    def driver(self) -> WebDriver:
        if self.__driver is None:
            raise RuntimeError(f"{self.__class__.__name__} must be used within a context manager to use the driver.")
        return self.__driver

    def scrape_all_lectures(self) -> None:
        logger.info('Collecting lecture URLs...')
        self.get_all_lecture_urls()
        self.assign_numbers()

        logger.info('Collecting lecture file URLs...')
        for lecture in self.lectures[self.lecture_indices]:
            logger.info(f'Collecting file URLs for {lecture.title}')
            lecture.file_infos = self.get_lecture_files(lecture.url)

    def assign_numbers(self) -> None:
        earliest_date = min(lecture.date for lecture in self.lectures)
        # {course: {week_number: [lectures]}}
        grouped_by_weeks: defaultdict[str, defaultdict[int, list[Echo360Lecture]]] = defaultdict(
            lambda: defaultdict(list))

        for lecture in self.lectures:
            lecture.week_number = ((lecture.date - earliest_date).days // 7) + 1
            grouped_by_weeks[lecture.course_name][lecture.week_number].append(lecture)

        for lectures in list(grouped_by_weeks.values())[0].values():
            for i, lecture in enumerate(lectures, 1):
                lecture.lecture_in_week = i

        course_name = self.lectures[0].course_name
        if course_name in self.config.conversion_table:
            for lecture in self.lectures:
                lecture.course_name = self.config.conversion_table[course_name].get(lecture.lecture_in_week,
                                                                                    course_name)
                grouped_by_weeks[course_name][lecture.week_number].remove(lecture)
                grouped_by_weeks[lecture.course_name][lecture.week_number].append(lecture)

            for course_lectures in grouped_by_weeks.values():
                for week_lectures in course_lectures.values():
                    for i, lecture in enumerate(week_lectures, 1):
                        lecture.lecture_in_week = i

    def get_all_lecture_urls(self) -> None:
        course_name = self.get_course_name()
        self.driver.get(self.course_url)
        elements_of_lectures: list[WebElement] = (WebDriverWait(self.driver, 10)
        .until(
            ec.presence_of_all_elements_located(self.config.locators.lectures)))

        for element in elements_of_lectures:
            lecture = Echo360Lecture()
            lecture.course_name = course_name

            date_string = element.find_element(*self.config.locators.lecture_date).text
            start_time_string, end_time_string = element.find_element(*self.config.locators.lecture_time).text.split(
                '-')

            lecture.date = dt.strptime(date_string, self.config.formats.date_format)
            lecture.start_time = dt.strptime(start_time_string, self.config.formats.time_format)
            lecture.end_time = dt.strptime(end_time_string, self.config.formats.time_format)

            lecture_id = element.get_attribute(self.config.attributes.lecture_id_attribute)
            lecture.url = self.config.formats.lecture_url.format(lecture_id=lecture_id)

            self.lectures.append(lecture)

    def get_lecture_files(self, lecture_url: str, timeout_seconds: int = 4) -> list[FileInfo]:
        self.driver.get(lecture_url)
        self.driver.get_log('performance')
        lecture_file_infos: dict[str, FileInfo] = {}
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout_seconds:
                break

            for entry in self.driver.get_log('performance'):
                message = self.get_message_attribute(entry)

                if message['method'] != 'Network.responseReceived':
                    continue

                response_url = message['params']['response']['url']
                response_file_name = os.path.basename(urlparse(response_url).path)

                if response_file_name in self.searched_files:
                    lecture_file_infos.setdefault(response_file_name, FileInfo(response_file_name, response_url))

                if len(lecture_file_infos) == len(self.searched_files):
                    break
            else:
                continue
            break

        return list(lecture_file_infos.values())

    def get_course_name(self) -> str:
        self.driver.get(self.course_url)
        heading_element: WebElement = (WebDriverWait(self.driver, 10)
                                       .until(ec.presence_of_element_located(self.config.locators.course_name)))
        course_name: str = self.driver.execute_script('return arguments[0].childNodes[2].textContent;',
                                                      heading_element).strip()

        return course_name

    def __enter__(self) -> Self:
        self.__setup_driver()
        return self

    def __exit__(self,
                 exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: TracebackType | None) -> None:
        self.driver.quit()
        self.__driver = None

    @staticmethod
    def get_message_attribute(entry: dict[str, Any]) -> dict[str, Any]:
        response: dict[str, Any] = json.loads(entry['message'])['message']
        return response

    def __setup_driver(self) -> None:
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        self.__driver = WebDriver(options=options)
