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
