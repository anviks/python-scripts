import logging
import os
import time
from typing import Any, Literal

import httplib2
import jsonpickle
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from googleapiclient.errors import ResumableUploadError
from googleapiclient.http import MediaFileUpload, HttpRequest, MediaUploadProgress

logger = logging.getLogger(__name__)

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 5

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = 'client_secret.json'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'

SCOPES = [
    'https://www.googleapis.com/auth/youtube'
]
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

TOKEN_PATH = 'token.json'


def get_new_token():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    return flow.run_local_server()


class YouTubeUploader:
    def __init__(self):
        self.youtube_resource: Resource | None = None
        self.insert_request: HttpRequest | None = None
        self.quota_used = 0
        self.quota_exceeded = False
        self.authorize()

    def authorize(self):
        creds: Credentials | None = None

        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    creds = get_new_token()
            else:
                creds = get_new_token()

            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())

        self.youtube_resource: Resource = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
        
    def find_playlist(self, name: str) -> str | None:
        """Find a playlist by name. Quota cost: 1 unit per page."""
        response = self._get_playlist_response()
        if playlist := self._search_for_playlist(response, name):
            return playlist
        
        while next_page_token := response.get('nextPageToken'):
            response = self._get_playlist_response(next_page_token)
            if playlist := self._search_for_playlist(response, name):
                return playlist

    def _get_playlist_response(self, page_token: str | None = None) -> dict[str, Any]:
        self.quota_used += 1
        return self.youtube_resource.playlists().list(
            part='id,snippet',
            mine=True,
            pageToken=page_token,
            maxResults=50
        ).execute()
    
    @staticmethod
    def _search_for_playlist(playlists_response: dict[str, Any], name: str) -> str | None:
        for playlist in playlists_response['items']:
            if playlist['snippet']['title'] == name:
                return playlist['id']
            
    def create_playlist(self, name: str, privacy: Literal['public', 'unlisted', 'private']) -> str:
        """Create a new playlist. Quota cost: 50 units."""
        playlist = self.youtube_resource.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': name
                },
                'status': {
                    'privacyStatus': privacy
                }
            }
        ).execute()
        self.quota_used += 50
        
        return playlist['id']
        
    def prepare_upload_request(
            self, 
            video_title: str, 
            file_path: str, 
            category_id: int,
            description: str = '',
            tags: list[str] | None = None) -> HttpRequest:
        request_body = {
            "snippet": {
                "title": video_title,
                "description": description,
                "tags": tags or [],
                "categoryId": str(category_id)
            },
            "status": {
                "privacyStatus": "unlisted",
                "selfDeclaredMadeForKids": False
            }
        }
        
        return self.youtube_resource.videos().insert(
            part=",".join(request_body.keys()),
            body=request_body,
            media_body=MediaFileUpload(file_path, resumable=True)
        )

    def resumable_upload(self, insert_request: HttpRequest, remove_file: bool = False) -> str | None:
        """Upload a video. Quota cost: 1600 units."""
        response = None
        error = None
        retries = 0
        self.quota_used += 1600
        
        logger.info("Uploading video file...")
        while response is None:
            try:
                status: MediaUploadProgress | None
                response: dict[str, Any] | None
                status, response = insert_request.next_chunk()
                logger.info(f"Status: {jsonpickle.encode(status, unpicklable=False, make_refs=False)}")
                logger.debug(f"Response: {response}")
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f'A retriable HTTP error {e.resp.status} occurred:\n{e.content}'
                    response = None
                elif isinstance(e, ResumableUploadError):
                    logger.error('Quota exceeded! Exiting...')
                    self.quota_used -= 1600
                    self.quota_exceeded = True
                    return
                else:
                    raise
            except RETRIABLE_EXCEPTIONS as e:
                error = f'A retriable error occurred: {e}'
                response = None

            if error is not None:
                logger.error(error)
                retries += 1
                if retries > MAX_RETRIES:
                    logger.error('No longer attempting to retry.')
                    return 

                sleep_seconds = retries * 2
                logger.info(f'Sleeping {sleep_seconds} seconds and then retrying...')
                time.sleep(sleep_seconds)

        return self._handle_successful_upload(insert_request, remove_file, response)

    def add_to_playlist(self, playlist_id: str, video_id: str):
        """Add a video to a playlist. Quota cost: 50 units."""
        self.youtube_resource.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        ).execute()
        self.quota_used += 50

    def _handle_successful_upload(self, insert_request: HttpRequest, remove_file: bool, response: dict[str, Any]):
        if 'id' in response:
            logger.info(f"Video with an id of '{response['id']}' was successfully uploaded")
            if remove_file:
                self._delete_uploaded_file(insert_request)
            return response['id']
        else:
            logger.error('The upload failed with an unexpected response: %s' % response)
            return
    
    @staticmethod
    def _delete_uploaded_file(insert_request: HttpRequest):
        filename = insert_request.resumable._filename
        del insert_request.resumable  # Release the file handle
        os.remove(filename)
        logger.info(f'Removed {filename}')
        
        directory = os.path.dirname(filename)
        while not os.listdir(directory):
            os.rmdir(directory)
            logger.info(f'Removed {directory}')
            directory = os.path.dirname(directory)
