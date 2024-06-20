class PlaylistListResponse:
    kind: str
    etag: str
    nextPageToken: str = None
    prevPageToken: str = None
    pageInfo: 'PageInfo'
    items: list['Playlist']

    class PageInfo:
        totalResults: int
        resultsPerPage: int

    class Playlist:
        kind: str
        etag: str
        id: str
        snippet: 'Snippet'
        status: 'Status'
        contentDetails: 'ContentDetails'
        player: 'Player'
        localizations: dict[str, 'Localization']

        class Snippet:
            publishedAt: str
            channelId: str
            title: str
            description: str
            thumbnails: dict[str, 'Thumbnail']
            channelTitle: str
            tags: list[str]
            defaultLanguage: str
            localized: 'Playlist.Localization'
            defaultAudioLanguage: str

            class Thumbnail:
                url: str
                width: int
                height: int

        class Status:
            privacyStatus: str

        class ContentDetails:
            itemCount: int

        class Player:
            embedHtml: str

        class Localization:
            title: str
            description: str
