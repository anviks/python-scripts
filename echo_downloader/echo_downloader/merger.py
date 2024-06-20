import logging
import os
import subprocess
from functools import partial
from multiprocessing import Pool

from .domain import Echo360Lecture
from .config_wrapper import EchoDownloaderConfig

logger = logging.getLogger(__name__)


def merge_files_concurrently(config: EchoDownloaderConfig, output_dir: str, lectures: list[Echo360Lecture],
                             delete_originals: bool = True) -> None:
    file_infos = get_file_infos(config, output_dir, lectures)

    with Pool() as pool:
        list(pool.imap_unordered(merge_files_wrapper, file_infos))

    if delete_originals:
        directories = set()

        for info in file_infos:
            for key, path in info.items():
                if key == 'output_path':
                    continue
                if os.path.exists(path):
                    os.remove(path)
                directories.add(os.path.dirname(path))

        for directory in directories:
            if not os.listdir(directory):
                os.rmdir(directory)


def merge_files_wrapper(file_info: dict[str, str]) -> None:
    merge_files(**file_info)


def merge_files(*, audio_path: str, video_path: str, output_path: str) -> None:
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', audio_path,
        '-i', video_path,
        '-c:a', 'copy',
        '-c:v', 'copy',
        output_path
    ]

    try:
        process = subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f'Merging completed successfully! ({audio_path} + {video_path} => {output_path})')
        logger.debug('Process:', process)
    except subprocess.CalledProcessError as e:
        logger.exception('Error while merging:', e)


def get_file_infos(config: EchoDownloaderConfig, output_dir: str, lectures: list[Echo360Lecture]) -> list[dict[str, str]]:
    file_infos = []

    for lecture in lectures:
        week_folder = os.path.join(output_dir, lecture.encoded_course_name, f'week_{lecture.week_number}')
        folder_join = partial(os.path.join, week_folder)
        file_names = {info.file_name for info in lecture.file_infos}

        for title_suffix, av_pairs in config.file_pairs.items():
            output_path = folder_join(lecture.encoded_title + title_suffix + '.mp4')

            for audio, video in av_pairs:
                if audio in file_names and video in file_names:
                    kwargs = dict(audio_path=folder_join(f'lecture_{lecture.lecture_in_week}', audio),
                                  video_path=folder_join(f'lecture_{lecture.lecture_in_week}', video),
                                  output_path=output_path)

                    file_infos.append(kwargs)
                    break

    return file_infos
