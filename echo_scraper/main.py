import asyncio
import logging
import sys
from argparse import ArgumentParser, ArgumentTypeError

import yaml
from plyer import notification
from utils_anviks import dict_to_object

from echo_scraper.config_wrapper import EchoConfig
from echo_scraper.downloader import download_files_from_urls
from scraper import EchoScraper
from merger import merge_files_concurrently


def slice_type(s) -> slice:
    try:
        parts = s.split(':')
        if len(parts) < 2:
            raise ValueError
        start = int(parts[0]) if parts[0] else None
        stop = int(parts[1]) if parts[1] else None
        step = int(parts[2]) if len(parts) > 2 and parts[2] else None

        return slice(start, stop, step)
    except ValueError:
        raise ArgumentTypeError("Invalid slice format. Must be start:stop[:step]. "
                                "This follows python's slice rules, meaning that start and stop can be omitted, "
                                "but the colon must be present.")


def main() -> None:
    sys.argv.extend(['-s', '40:', '-sub', 'Tarkvaratehnika', '-o', r'C:\Users\Andreas Viks\Downloads', '-n'])

    with open('config.yaml') as f:
        config = dict_to_object(yaml.safe_load(f), EchoConfig)
        
    logging.basicConfig(
        level=config.logging.level,
        format=config.logging.format,
        datefmt=config.logging.datefmt
    )

    parser = ArgumentParser(description='Echo360 video downloader')
    parser.add_argument('-s', '--slice', type=slice_type,
                        help='Slice object in the format start:stop[:step], will be used to slice the list of lectures',
                        required=True)
    parser.add_argument('-sub', '--subject', type=str, choices=config.course_abbreviations.keys(),
                        help='Subject for which to download lectures', required=True)
    parser.add_argument('-o', '--output', type=str, default='.', help='Output directory')
    parser.add_argument('-n', '--notify', action='store_true', help='Send a notification after the script finishes')
    args = parser.parse_args()

    full_course_title = config.course_abbreviations[args.subject]

    with EchoScraper(config, full_course_title, args.slice, headless=True) as scraper:
        scraper.scrape_all_lectures()
        lectures = scraper.lectures

    asyncio.run(download_files_from_urls(args.output, lectures))
    merge_files_concurrently(config, args.output, lectures)

    if args.notify:
        notification.notify(
            title='Echo Scraper',
            message='Lectures downloaded successfully',
            timeout=10
        )


if __name__ == '__main__':
    main()
