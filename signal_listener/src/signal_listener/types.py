from typing import NotRequired, TypedDict


class TypingMessage(TypedDict):
    action: str
    timestamp: int
    groupId: NotRequired[str]


class GroupInfo(TypedDict):
    groupId: str
    groupName: str
    revision: int
    type: str


class Reaction(TypedDict):
    emoji: str
    targetAuthor: str
    targetAuthorNumber: str
    targetAuthorUuid: str
    targetSentTimestamp: int
    isRemove: bool


class DataMessage(TypedDict):
    timestamp: int
    message: str | None
    expiresInSeconds: int
    isExpirationUpdate: bool
    viewOnce: bool
    isEndSession: bool
    isProfileKeyUpdate: bool
    hasProfileKey: bool
    groupInfo: NotRequired[GroupInfo]
    reaction: NotRequired[Reaction]


class Envelope(TypedDict):
    source: str
    sourceNumber: str | None
    sourceUuid: str
    sourceName: str
    sourceDevice: int
    timestamp: int
    serverReceivedTimestamp: int
    serverDeliveredTimestamp: int
    typingMessage: NotRequired[TypingMessage]
    dataMessage: NotRequired[DataMessage]


class ModelItem(TypedDict):
    envelope: Envelope
    account: str


class Config(TypedDict):
    api_url: str
    trigger_msg: str
    msg_count: int
    emoji_count: int
    window: int
    cooldown: int
    channels: list[str]
