# %%

# Standard Lib
from dataclasses import dataclass
from typing import Any

# External
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource

# Types
ResourceYoutubeV3 = Resource
JSON = dict[str, Any]

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

    def __str__(self) -> str:
        return f"{self.authorDisplayName}: {self.textDisplay}"


def process_comments(response: JSON) -> list[Comment]:
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
            part="id,replies,snippet", videoId=videoID, pageToken=pageToken
        )
        response = request.execute()
        comments.extend(process_comments(response))
        if "nextPageToken" in response:
            pageToken = response["nextPageToken"]
        else:
            break

    return comments


def create_youtube_client() -> ResourceYoutubeV3:
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=[
            "https://www.googleapis.com/auth/youtube.force-ssl",
        ],
    )
    youtube = build("youtube", "v3", credentials=creds)
    return youtube


# %%
youtube = create_youtube_client()
comments = comment_threads(youtube, "XTjtPc0uiG8")
