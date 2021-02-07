# GCS Inspector
GCS Inspector is a simple library that checks for public storage and objects attached to a Google Service Account

## Notable features
  - Slack Integration
  - Parseable output
  - Update detection

## Requirements
1. Google Service Account file
2. Python 3.8
3. Pip

## Usage
#### Manual - Using Github Repo
    1. Clone this repo
    2. Create a Google service account for your project and download the json authentication file (it should look like: `projectname.json`)
    3. Create a virtual environment
        `virtualenv venv && source venv/bin/activate`
    4. Install the required libraries
        `pip install -r requriements.txt`
    5. Run the program by supplying the service account json authentication file
        `python3.8 -m gcs-inspector projectname.json`
    6. (Optional) Set up a cronjob for regular monitoring

#### Using Pip (In progress)
    1. Create a Google service account for your project and download the json authentication file (it should look like: `projectname.json`)
    2. Install the library
        `pip install gcs-inspector`
    3. Use the library
        `gcs-inspector projectname.json`
    4. (Optional) Set up a cronjob for regular monitoring

## Options
    -h, --help            show this help message and exit
    -s, --skip_object     skip object-level checking (so only bucket-level are checked)
    -x, --silent          disable writing to screen (except errors)
    -u WEBHOOK_URL, --webhook_url WEBHOOK_URL
                          send results to this slack webhook url
    -l, --log             enable output to the filename described
    -f FILENAME, --filename FILENAME
                            change filename output
    -o FOLDER, --out_folder FOLDER
                            change folername output
    -m {0,1,2}, --mode {0,1,2}
                            0: Normal text
                            1: Slack-formatted
                            2: Only get difference from previous state (display mode 1)

## Contributing and Issues
Contributions to this project will be much appreciated :)

#### How to Contribute
The entrypoint of the code is in `gcs_inspector/__main__.py`. 
Besides there, the bulk of the code is mainly in `gcs_inspector/bucket_processor.py`.
