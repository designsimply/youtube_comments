# %%

# standard
from dataclasses import dataclass
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor

# external
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from google.cloud import language_v2


# types
ResourceYoutubeV3 = Resource
ResourceLanguage = Resource
JSON = dict[str, Any]
Filepath = str


class config:
    """Configuration"""

    CREDENTIALS_FILE: Filepath = "credentials.json"
    MAX_WORKERS: int = 5


# %%


@dataclass
class Comment:
    """Youtube Comment"""

    channelId: str
    videoId: str
    textDisplay: str
    # textOriginal: str
    authorDisplayName: str
    authorProfileImageUrl: str
    authorChannelUrl: str
    authorChannelId: str
    canRate: bool
    viewerRating: str
    likeCount: int
    publishedAt: str
    updatedAt: str
    parentId: str
    commentId: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Comment":
        return cls(
            channelId=data["channelId"],
            videoId=data["videoId"],
            textDisplay=data["textDisplay"],
            # textOriginal=data["textOriginal"],
            authorDisplayName=data["authorDisplayName"],
            authorProfileImageUrl=data["authorProfileImageUrl"],
            authorChannelUrl=data["authorChannelUrl"],
            authorChannelId=data["authorChannelId"]["value"],
            canRate=data["canRate"],
            viewerRating=data["viewerRating"],
            likeCount=data["likeCount"],
            publishedAt=data["publishedAt"],
            updatedAt=data["updatedAt"],
            parentId=data["parentId"],
            commentId=data["commentId"],
        )

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    def __str__(self) -> str:
        return f"{self.authorDisplayName}: {self.commentId}"


def parse_comments(response: JSON) -> list[Comment]:
    comments = []
    for res in response["items"]:
        # loop through the replies
        if "replies" in res.keys():
            for reply in res["replies"]["comments"]:
                comment = reply["snippet"]
                comment["commentId"] = reply["id"]
                comments.append(Comment.from_dict(comment))
        else:
            comment = {}
            comment["snippet"] = res["snippet"]["topLevelComment"]["snippet"]
            comment["snippet"]["parentId"] = None
            comment["snippet"]["commentId"] = res["snippet"]["topLevelComment"]["id"]
            comments.append(Comment.from_dict(comment["snippet"]))
    return comments


def comment_threads(youtube: ResourceYoutubeV3, videoID: str) -> list[Comment]:
    comments = []
    pageToken = None
    while True:
        request = youtube.commentThreads().list(
            part="id,replies,snippet",
            videoId=videoID,
            pageToken=pageToken,
        )
        response = request.execute()
        comments.extend(parse_comments(response))
        if "nextPageToken" in response:
            pageToken = response["nextPageToken"]
        else:
            break

    return comments


def create_youtube_client() -> ResourceYoutubeV3:
    creds = service_account.Credentials.from_service_account_file(
        config.CREDENTIALS_FILE,
        scopes=[
            "https://www.googleapis.com/auth/youtube.force-ssl",
        ],
    )
    youtube = build("youtube", "v3", credentials=creds)
    return youtube


# %%


def create_language_client() -> ResourceLanguage:
    creds = service_account.Credentials.from_service_account_file(
        config.CREDENTIALS_FILE,
        scopes=[
            "https://www.googleapis.com/auth/cloud-language",
        ],
    )
    return language_v2.LanguageServiceClient(credentials=creds)


@dataclass
class Sentiment:
    """Sentiment Analysis Result"""

    score: float
    magnitude: float


def get_sentiment(client: ResourceLanguage, text: str, lang: str = "en") -> Sentiment:
    response = client.analyze_sentiment(
        request={
            "document": {
                "content": text,
                "type_": language_v2.Document.Type.PLAIN_TEXT,
                "language_code": lang,
            },
            "encoding_type": language_v2.EncodingType.UTF8,
        }
    )
    sentiment = response.document_sentiment
    return Sentiment(score=sentiment.score, magnitude=sentiment.magnitude)


def get_sentiments(
    client: ResourceLanguage, comments: list[Comment]
) -> list[Sentiment]:
    """Get Sentiments in Parallel"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(
            executor.map(
                lambda c: get_sentiment(client, c.textDisplay),
                comments,
                chunksize=10,
            )
        )


# %%
youtube = create_youtube_client()
comments = comment_threads(youtube, "XTjtPc0uiG8")


# %%

lang = create_language_client()
sentiments = get_sentiments(lang, comments[:5])

# %%
