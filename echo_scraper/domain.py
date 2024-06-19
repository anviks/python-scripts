import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime


# "[10.04.2024 - 10:00-11:30] Introduction to Biology #5 | Screen Recording"

@dataclass(slots=True, eq=False)
class FileInfo:
    file_name: str
    url: str = ''
    local_path: str = ''


@dataclass(init=True, slots=True)
class Echo360Lecture:
    date: datetime | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    course_name: str = ''
    url: str = ''
    week_number: int = 0
    lecture_in_week: int = 0
    file_infos: list[FileInfo] = field(default_factory=list)

    @property
    def lecture_identifier(self) -> str:
        return f'{self.week_number}.{self.lecture_in_week}'

    @property
    def title(self) -> str:
        return f'[{self.date:%d.%m.%Y} - {self.start_time:%H:%M}-{self.end_time:%H:%M}] {self.course_name} #{self.lecture_identifier}'

    @property
    def encoded_title(self) -> str:
        return urllib.parse.quote(self.title, safe=' #[]')

    @property
    def encoded_course_name(self) -> str:
        return urllib.parse.quote(self.course_name, safe=' #[]')
