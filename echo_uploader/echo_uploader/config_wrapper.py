from typing import Literal


class EchoUploaderConfig:
    logging: 'Logging'
    course_abbreviations: dict[str, str]
    
    class Logging:
        level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        format: str
        datefmt: str
