import time
import urllib
import base64
import hmac
import sha
import os
import flask
import json
from fnmatch import fnmatch

app = flask.Flask(__name__)

# Env variables
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS')
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION')
S3_BUCKET = os.environ.get('S3_BUCKET')


def cors_headers_for(origin):
    cors_headers = {
        'Access-Control-Allow-Origin': 'null', 
        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
    }
    if origin and any(fnmatch(origin, allowed_origin) for allowed_origin in ALLOWED_ORIGINS):
        cors_headers['Access-Control-Allow-Origin'] = origin
    return cors_headers


@app.route('/')
def sign_s3():
    if None in [AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET]:
        return json.dumps({"error": "No AWS Creds"}), 500

    object_name = flask.request.args.get('object_name')
    if not any(object_name.endswith(extension) for extension in ALLOWED_EXTENSIONS):
        return json.dumps({"error": "Invalid extension. We only allow {}".format(ALLOWED_EXTENSIONS)}), 403

    mime_type = flask.request.args.get('object_type')
    expires = int(time.time() + 100)
    amz_headers = "x-amz-acl:public-read"
    put_request = "PUT\n\n%s\n%d\n%s\n/%s/%s" % (mime_type,
                                                 expires, amz_headers, S3_BUCKET, object_name)
    signature = base64.encodestring(
        hmac.new(AWS_SECRET_KEY, put_request, sha).digest())
    signature = urllib.quote_plus(signature.strip())

    url = 'https://%s.s3-%s.amazonaws.com/%s' % (S3_BUCKET,
                                                 AWS_REGION, object_name)

    return json.dumps({
        'signed_request': '%s?AWSAccessKeyId=%s&Expires=%d&Signature=%s' % (url, AWS_ACCESS_KEY, expires, signature),
        'url': url
    }), 200, cors_headers_for(flask.request.headers.get('Origin'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
