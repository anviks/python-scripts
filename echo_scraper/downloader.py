import asyncio
import logging
import os

import aiofiles
import aiohttp

from echo_scraper.domain import Echo360Lecture

logger = logging.getLogger(__name__)


async def download_files_from_urls(output_dir: str, lectures: list[Echo360Lecture]) -> None:
    logger.info('Downloading files...')
    async with aiohttp.ClientSession() as session:
        # Initial request to get the cookies
        await session.get('https://echo360.org.uk/section/3b6b058c-10d1-4732-a414-3b8901fbffec/public')

        tasks = []
        for lecture in lectures:
            if not lecture.file_infos:
                continue
            
            folder = os.path.join(output_dir, lecture.encoded_course_name, f'week_{lecture.week_number}', f'lecture_{lecture.lecture_in_week}')
            os.makedirs(folder, exist_ok=True)
            
            for info in lecture.file_infos:
                if info.url is None:
                    continue
                destination_path = os.path.join(folder, info.file_name)
                info.local_path = os.path.abspath(destination_path)
                task = asyncio.create_task(download_file(session, destination_path, info.url))
                tasks.append(task)              

        await asyncio.gather(*tasks, return_exceptions=True)
    logger.info('All files downloaded')


async def download_file(session: aiohttp.ClientSession, destination_path: str, url: str) -> None:
    try:
        async with session.get(url, timeout=30 * 60) as response:
            # Return if the file already exists
            if os.path.exists(destination_path) and os.path.getsize(destination_path) == int(response.headers.get('Content-Length', 0)):
                return
            response.raise_for_status()
            async with aiofiles.open(destination_path, 'wb') as f:
                async for chunk in response.content.iter_any():
                    await f.write(chunk)
    except aiohttp.ClientError as e:
        logger.error(f"Failed to download {url}: {e}")
        await asyncio.sleep(0)  # Yield to the event loop to prevent blocking
