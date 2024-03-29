import unittest
import json
import uuid
from freezegun import freeze_time

import application

class SigningTest(unittest.TestCase):
    def setUp(self):
        application.AWS_ACCESS_KEY = 'access-key'
        application.AWS_SECRET_KEY = 'secret-key'
        application.AWS_REGION = 'ap-southeast-2'
        application.S3_BUCKET = 'jumpin-media'
        application.ALLOWED_EXTENSIONS = '.jpg,.gif,.png'
        application.ALLOWED_ORIGINS = ['http://jumpin-*.elasticbeanstalk.com', 'http://jumpin.com.au']
        def canned_uuid():
            return uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
        uuid.uuid4 = canned_uuid
        self.app = application.application.test_client()

    def test_root(self):
        '''Should return an error if no object_name was provided'''
        resp = self.app.get('/')
        self.assertEqual(resp.status_code, 400)
        obj = json.loads(resp.data)
        self.assertIn('object_name', obj['error'])

    def test_invalid_extension(self):
        '''Should not generate a signature if the file extension is invalid'''
        resp = self.app.get('/?object_name=test.exe&object_type=image/jpg')
        self.assertEqual(resp.status_code, 403)

    def test_missing_creds(self):
        '''Should return a 500 if the AWS credentials are missing'''
        original_access_key = application.AWS_ACCESS_KEY
        application.AWS_ACCESS_KEY = None
        resp = self.app.get('/?object_name=test.jpg&object_type=image/jpg')
        self.assertEqual(resp.status_code, 500)
        err = json.loads(resp.data)
        self.assertEqual(err['error'], 'No AWS Creds')
        application.AWS_ACCESS_KEY = original_access_key

    def test_valid_extension(self):
        '''Should generate a URL and a signature if the extension is valid'''
        resp = self.app.get('/?object_name=test.jpg&object_type=image/jpg')
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.data)
        self.assertEqual(obj.get('url'), 'https://jumpin-media.s3-ap-southeast-2.amazonaws.com/test-00010203-0405-0607-0809-0a0b0c0d0e0f.jpg')
        self.assertIsNotNone(obj.get('signed_request'))

    def test_cors(self):
        '''Should return CORS=null if no origin header is provided'''
        resp = self.app.get('/?object_name=test.jpg&object_type=image/jpg')
        self.assertEqual(resp.headers['Access-Control-Allow-Origin'], 'null')

    def test_cors_incorrect_origin(self):
        '''Should return CORS=null if an incorrect Origin: header is provided'''
        resp = self.app.get('/?object_name=test.jpg&object_type=image/jpg', headers={'Origin': 'http://facebook.com'})
        self.assertEqual(resp.headers['Access-Control-Allow-Origin'], 'null')

    def test_cors_wildcard(self):
        '''Should return a dynamic Access-Control-Allow-Origin, if the Origin header matches any ALLOWED_ORIGINS'''
        resp = self.app.get('/?object_name=test.jpg&object_type=image/jpg', headers={'Origin': 'http://jumpin.com.au'})
        self.assertEqual(resp.headers['Access-Control-Allow-Origin'], 'http://jumpin.com.au')

    def test_cors_localhost(self):
        '''Should return Access-Control-Allow-Origin: localhost for local testing'''
        resp = self.app.get('/?object_name=test.jpg&object_type=image/jpg', headers={'Origin': 'http://localhost:5000'})
        self.assertEqual(resp.headers['Access-Control-Allow-Origin'], 'http://localhost:5000')

    def test_signature_expiry(self):
        '''Should expire the signature in 100 seconds'''
        with freeze_time('2014-01-01'):
            resp = self.app.get('/?object_name=test.jpg&object_type=image/jpg')
            obj = json.loads(resp.data)
            self.assertIn('Expires=1388530900', obj['signed_request'])

    def test_signature(self):
        '''Should generate the correct signature using the fancy HMAC-SHA1'''
        with freeze_time('2014-01-01'):
            resp = self.app.get('/?object_name=test.jpg&object_type=image/jpg')
            obj = json.loads(resp.data)
            self.assertTrue(obj['signed_request'].endswith('Signature=Ko0P7%2F0wQbAOynxn22X3WkBC7eM%3D'))

