from dataclasses import dataclass


@dataclass
class SourceFile:
    name: str = ''
    extension: str = ''
    template_name: str = ''
    contents: str = ''


@dataclass
class KataDetails:
    title: str
    slug: str
    difficulty: int | None
    description: str
    files: list[SourceFile]
