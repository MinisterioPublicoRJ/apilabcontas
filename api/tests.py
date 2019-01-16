from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from hashlib import md5
from io import BytesIO
from unittest import mock
from .utils import securedecorator, md5reader

# Create your tests here.

@securedecorator
def postmethod(request):
    pass

class TestSecureDecorator(TestCase):
    def test_secure_empty_key(self):
        fakerequest = RequestFactory().post('')

        with self.assertRaises(PermissionDenied):
            postmethod(request=fakerequest)

    def test_secure_wrong_key(self):
        fakerequest = RequestFactory().post(
            '',
            data={'SECRET': 'wrongkey'}
        )
        

        with self.assertRaises(PermissionDenied):
            postmethod(request=fakerequest)


    def test_secure(self):
        fakerequest = RequestFactory().post(
            '',
            data={'SECRET': settings.SECRET}
        )
        
        postmethod(request=fakerequest)


class TestMd5Reader(TestCase):
    def test_hexdigest(self):
        contents = b'filecontents'
        uploadedfile = SimpleUploadedFile(
            'file',
            contents
        )

        self.assertEquals(
            md5reader(uploadedfile),
            md5(contents).hexdigest()
        )

        self.assertEqual(uploadedfile.tell(), 0)

    def test_wronghexdigest(self):
        uploadedfile = SimpleUploadedFile(
            'file',
            b'filecontents'
        )

        self.assertNotEquals(
            md5reader(uploadedfile),
            md5(b'lerolero').hexdigest()
        )

class TestUpload(TestCase):
    @mock.patch('api.views.upload_to_hdfs')
    def test_file_post(self, upload_to_hdfs):
        contents = b'filecontents'

        contents_md5 = md5(contents).hexdigest()
        contents_file = BytesIO()
        contents_file.write(contents)
        contents_file.seek(0)

        response = self.client.post(
            reverse('api-upload'),
            {
                'SECRET': settings.SECRET,
                'md5': contents_md5,
                'method': 'cpf',
                'file': contents_file
            }
        )

        self.assertEquals(response.status_code, 201)
        self.assertEquals(response.json()['md5'], contents_md5)
        upload_to_hdfs.assert_called_once()

    @mock.patch('api.views.upload_to_hdfs')
    def test_file_post_wrong_md5(self, upload_to_hdfs):
        contents = b'filecontents'

        contents_md5 = md5(contents).hexdigest()
        contents_file = BytesIO()
        contents_file.write(contents)
        contents_file.seek(0)

        response = self.client.post(
            reverse('api-upload'),
            {
                'SECRET': settings.SECRET,
                'md5': 'wrongmd5',
                'method': 'cpf',
                'file': contents_file
            }
        )

        self.assertEquals(response.status_code, 500)
        self.assertEquals(response.json()['md5'], contents_md5)
        upload_to_hdfs.assert_not_called()
