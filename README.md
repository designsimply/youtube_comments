# YouTube Comment Getter

This script extracts YouTube comments.

# Getting Started

## Python Environment

`make install`

## Google Credentials

You'll need a [Google project](https://developers.google.com/workspace/guides/create-project).

Within the Google project go to menu, select "API & Services" then "Credentials". URL is something like `https://console.cloud.google.com/apis/credentials?project={your project id}`. Under "Service Accounts", select "Manage service accounts" then a new page will load. After this page loads click "+ CREATE SERVICE ACCOUNT" at the top. Name it whatever you'd like. Permissions are optional but I selected "Basic --> Viewer" because I only want to read. Once created go back to the "Manage service accounts" page and select the new account you made.

Within the new account, you'll have several tabs and select "Keys". When that tab loads click "Add Key" and "Create new key". This should create a file which will download. This file is your credentials.json file. 

Move that file to this folder and rename to credentials.json. 

# Start

``` bash
source .venv/bin/activate
python comments.py --video-id TAhbFRMURtg
```

# Sentiment Analysis

If you want to run sentiment analysis on comments too (`python comments.py --video-id TAhbFRMURtg
 --include-sentiment`) then you'll need to enable this for the project you set up eariler.

This will take you to enabling NLP if you put in your projectId.
`https://console.cloud.google.com/apis/enableflow?apiid=language.googleapis.com&authuser=1&project={projectId}`

Learn more about setting up [google NLP](https://cloud.google.com/python/docs/reference/language/latest)
