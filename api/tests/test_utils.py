import gzip

from hashlib import md5
from unittest import mock

from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from model_mommy.mommy import make

from api.utils import securedecorator, md5reader, is_header_valid


@securedecorator
def postmethod(request):
    pass


class TestSecureDecorator(TestCase):
    def test_secure_empty_key(self):
        fakerequest = RequestFactory().post('')

        with self.assertRaises(PermissionDenied):
            postmethod(request=fakerequest)

    def test_empty_username(self):
        secret = make('secret.Secret', username='anyname')
        fakerequest = RequestFactory().post(
            '',
            data={'SECRET': secret.secret_key}
        )

        with self.assertRaises(PermissionDenied):
            postmethod(fakerequest)

    def test_secure_wrong_key(self):
        make(
            'secret.Secret',
            username='anyname',
        )
        fakerequest = RequestFactory().post(
            '',
            data={
                'nome': 'anyname',
                'SECRET': 'wrongkey'
            }
        )

        with self.assertRaises(PermissionDenied):
            postmethod(request=fakerequest)

    def test_secure_user_doesnt_match_secret(self):
        make(
            'secret.Secret',
            username='anyname',
        )
        fakerequest = RequestFactory().post(
            '',
            data={
                'nome': 'othername',
                'SECRET': 'aaaabbbcc'
            }
        )

        with self.assertRaises(PermissionDenied):
            postmethod(request=fakerequest)

    def test_secure(self):
        secret = make(
            'secret.Secret',
            username='anyname',
        )
        fakerequest = RequestFactory().post(
            '',
            data={'nome': secret.username, 'SECRET': secret.secret_key}
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

        self.assertEqual(uploadedfile.file.tell(), 0)

    def test_wronghexdigest(self):
        uploadedfile = SimpleUploadedFile(
            'file',
            b'filecontents'
        )

        self.assertNotEquals(
            md5reader(uploadedfile),
            md5(b'lerolero').hexdigest()
        )


class TestValidHeader(TestCase):
    @mock.patch('secret.models.send_mail')
    def test_validate_file_header(self, _send_mail):
        gzipped_file = open('api/tests/csv_example.csv.gz', 'rb')
        secret = make('secret.Secret', username='anyname')
        mmap = make(
            'methodmapping.MethodMapping',
            method='cpf',
            uri='/path/to/storage/cpf',
            mandatory_headers='field1,field2,field3'
        )
        secret.methods.add(mmap)

        valid, status = is_header_valid(secret.username, 'cpf', gzipped_file)
        import ipdb;ipdb.set_trace()

        self.assertTrue(valid)
