import logging
import os
import urllib.parse
from argparse import ArgumentParser, Namespace
from os.path import join, isdir

import platformdirs
import yaml
from googleapiclient.http import HttpRequest
from utils_anviks import dict_to_object

from .config_wrapper import EchoUploaderConfig
from .upload import YouTubeUploader
from .youtube_constants import Category


def get_playlist_id(uploader: YouTubeUploader, course: str) -> str | None:
    playlist_id = uploader.find_playlist_id(name=course)

    if playlist_id is None:
        if input(f"Couldn't find the playlist '{course}'. Create it? (y/n) ").lower() != 'y':
            return
        playlist_id = uploader.create_playlist(name=course, visibility='unlisted')

    return playlist_id


def get_config(config_dir: str) -> EchoUploaderConfig:
    default_config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    custom_config_path = os.path.join(config_dir, 'config.yaml')

    with open(default_config_path) as f:
        file_contents = f.read()

    config_dict = yaml.safe_load(file_contents)

    if not os.path.exists(custom_config_path):
        os.makedirs(os.path.dirname(custom_config_path), exist_ok=True)
        with open(custom_config_path, 'w') as f:
            f.write(file_contents)
    else:
        with open(custom_config_path) as f:
            config_dict.update(yaml.safe_load(f))

    return dict_to_object(config_dict, EchoUploaderConfig)


def get_cli_args(config: EchoUploaderConfig) -> Namespace:
    parser = ArgumentParser(description='Echo360 video uploader')
    parser.add_argument('-c', '--course', type=str, choices=config.course_abbreviations.keys(),
                        help='Course of the videos to upload', required=True)
    parser.add_argument('-s', '--source', type=str, help='Source directory of the videos', default='.')
    
    return parser.parse_args()


def get_logger(config: EchoUploaderConfig) -> logging.Logger:
    logging.basicConfig(
        level=config.logging.level,
        format=config.logging.format,
        datefmt=config.logging.datefmt
    )
    
    return logging.getLogger(__name__)


def main() -> None:
    config_dir = platformdirs.user_config_dir('echo-uploader', 'anviks', roaming=True)
    client_secrets_path = os.path.join(config_dir, 'client_secrets.json')
    token_path = os.path.join(config_dir, 'token.json')
    
    config = get_config(config_dir)
    logger = get_logger(config)
    args = get_cli_args(config)

    full_course_title = config.course_abbreviations[args.course]

    uploader = YouTubeUploader(client_secrets_path, token_path)
    playlist_id: str = get_playlist_id(uploader, full_course_title)

    course_dir = join(args.source, urllib.parse.quote(full_course_title, safe=' #[]'))
    for folder in os.listdir(course_dir):
        week_dir = join(course_dir, folder)
        if not isdir(week_dir):
            continue

        for video in os.listdir(week_dir):
            if not video.endswith('.mp4'):
                continue

            video_path = join(week_dir, video)
            if isdir(video_path):
                continue

            video_title: str = urllib.parse.unquote(video)[:-len('.mp4')]
            request: HttpRequest = uploader.prepare_upload_request(
                video_title=video_title,
                file_path=video_path,
                description='Uploaded by a script.',
                category_id=Category.EDUCATION)
            video_id: str = uploader.resumable_upload(request, remove_file=True)

            if video_id is None:
                break

            uploader.add_to_playlist(playlist_id, video_id)
        else:
            continue
        break

    logger.info('Finished uploading videos')
    logger.info(f'Quota used: {uploader.quota_used}')


if __name__ == '__main__':
    main()
