# %%

# standard
from dataclasses import dataclass
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor
import csv
from argparse import ArgumentParser
import logging

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
    """Configuration. Should probably eventually be a module."""

    CREDENTIALS_FILE: Filepath = "credentials.json"
    MAX_WORKERS: int = 5

    logging.basicConfig(level=logging.INFO)


logger = logging.getLogger(__name__)


# %%


@dataclass
class Comment:
    """Youtube Comment"""

    channelId: str
    videoId: str
    textDisplay: str
    # textOriginal: str # don't need both text fields
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


def comment_threads(youtube: ResourceYoutubeV3, videoID: str, limit: int = -1) -> list[Comment]:
    comments = []
    pageToken = None
    logger.info(f"Fetching comments for video {videoID}")
    while True:
        request = youtube.commentThreads().list(
            part="id,replies,snippet",
            videoId=videoID,
            pageToken=pageToken,
        )
        response = request.execute()
        comments.extend(parse_comments(response))
        if limit > 0 and len(comments) >= limit:
            break
        if "nextPageToken" in response:
            pageToken = response["nextPageToken"]
        else:
            break
    comments_limited = comments[:limit] if limit > 0 else comments
    logger.info(f"Found {len(comments_limited)} comments. Max: {limit}")
    return comments_limited


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
    client: ResourceLanguage,
    comments: list[Comment],
) -> list[Sentiment]:
    """Get Sentiments in Parallel"""
    logger.info("Fetching Sentiments")
    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(
            executor.map(
                lambda c: get_sentiment(client, c.textDisplay),
                comments,
                chunksize=10,
            )
        )


# %%


def to_csv(
    filepath: Filepath,
    comments: list[Comment],
    sentiments: Optional[list[Sentiment]] = None,
) -> None:
    """Write Comments to CSV File

    Args:
        filepath (Filepath): Filepath to write to
        comments (list[Comment]): List of comments
        sentiments (Optional[list[Sentiment]], optional): List of sentiments. Defaults to None.
    """
    logger.info(f"Writing comments to {filepath}")
    delimiter = "\t"

    rows = []
    for i, comment in enumerate(comments):
        row = comment.to_dict()
        row["textDisplay"] = comment.textDisplay.replace(delimiter, " ")
        if sentiments:
            row["score"] = sentiments[i].score
            row["magnitude"] = sentiments[i].magnitude
        rows.append(row)

    if len(rows) == 0:
        raise ValueError("No comments to write to file.")
    first_row = rows[0]

    with open(filepath, "w") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=first_row.keys(),
            delimiter=delimiter,
        )
        writer.writeheader()
        writer.writerows(rows)


# %%
def run(
    videoID: str,
    include_sentiment: bool,
    output_file: Optional[Filepath] = None,
    limit: int = 100,
) -> None:
    youtube = create_youtube_client()
    comments = comment_threads(youtube, videoID, limit=limit)
    if include_sentiment:
        lang = create_language_client()
        sentiments = get_sentiments(lang, comments)
    else:
        sentiments = None

    output = output_file or f"exports/{videoID}.tsv"
    to_csv(output, comments, sentiments)


def main():
    parse = ArgumentParser()
    parse.add_argument("--videoID", type=str, required=True)
    parse.add_argument("--include-sentiment", action="store_true")
    parse.add_argument("--limit", type=int, default=100, required=False)
    parse.add_argument("--output", type=str, required=False)

    pargs = parse.parse_args()
    output_file = f"exports/{pargs.videoID}.tsv" if not pargs.output else pargs.output
    video_id = pargs.videoID
    include_sentiment = pargs.include_sentiment
    limit = pargs.limit

    run(video_id, include_sentiment, output_file, limit)


# %%
if __name__ == "__main__":
    main()
    # run(
    #     videoID="__ABPkb0aF8",
    #     include_sentiment=True,
    # )

# %%
