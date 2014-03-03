
A service that signs requests for client-side media uploads.

Allows you to configure an s3 bucket and allowed file extensions.

# API

    GET /?object_name=awesome-pic.jpg&object_type=image/jpeg

Returns an object with `url` and `signed_request`. 

`signed_request` is the URL for a PUT request that is able to upload that media item.

`url` is the final URL that the item will be available at.

# Prerequisites

- Python 2.7
- Virtualenv

# Setup

    virtualenv venv --distribute
    venv/bin/pip install -r requirements.txt

# Running

You'll need to configure the following environment variables:

- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` for the AWS creds
- `S3_BUCKET` and `AWS_REGION` with the s3 bucket details
- `ALLOWED_EXTENSIONS`, a comma separated list of file types to allow client-side uploads, e.g. `.jpg,.png`
- (optionally) `ALLOWED_ORIGINS`, hosts to add to the `Access-Control-Allow-Origin` header, e.g. `jumpin.com.au`
- (optionally) `PORT`, the HTTP port to listen on (defaults to 8000)

To start the server, set the above env variables somehow, and run:

    venv/bin/python application.py

You should see a message when the server is started.

# Testing

    venv/bin/pip install -r test-requirements.txt
    venv/bin/nosetests -v

