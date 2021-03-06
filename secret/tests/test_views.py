from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse
from django.test import TestCase
from freezegun import freeze_time
from model_mommy.mommy import make

from secret.models import Secret


class SecretView(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(
            'anyuser', 'anyuser@email.com', 'anypwd'
        )
        self.client.login(username='anyuser', password='anypwd')

    def test_correct_response(self):
        url = reverse('secret:create-secret')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    @freeze_time('2019-03-12 12:00:00')
    def test_create_secret_key(self):
        url = reverse('secret:create-secret')
        data = {
            'username': 'anyname',
            'email': 'any@email.com'
        }
        resp = self.client.post(url, data=data)
        user = Secret.objects.last()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.username, 'anyname')
        self.assertEqual(user.email, 'any@email.com')
        self.assertEqual(user.secret_key, 'd3a4646728a9de9a74d8fc4c41966a42')
        self.assertEqual(
            resp.context['created_secret'],
            'd3a4646728a9de9a74d8fc4c41966a42'
        )
        messages = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertIn('Chave criada com sucesso!', messages)

    def test_template_used(self):
        url = reverse('secret:create-secret')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'secret/create-secret.html')

    def test_dont_duplicate_secret_user(self):
        make(Secret, username='anyname')
        url = reverse('secret:create-secret')
        data = {
            'username': 'anyname',
            'email': 'any@email.com'
        }
        resp = self.client.post(url, data=data)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('Usuário já existe!'.encode(), resp.content)

    def test_login_required(self):
        # Log user out
        self.client.logout()
        url = reverse('secret:create-secret')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)


class SecretList(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(
            'anyuser', 'anyuser@email.com', 'anypwd'
        )
        self.client.login(username='anyuser', password='anypwd')

    def test_correct_response(self):
        make(Secret, _quantity=2)
        url = reverse('secret:list-secret')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'secret/list-secret.html')
        self.assertEqual(resp.context['secrets'].count(), 2)

    def test_login_required(self):
        self.client.logout()
        url = reverse('secret:list-secret')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)


class SecretDelete(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(
            'anyuser', 'anyuser@email.com', 'anypwd'
        )
        self.client.login(username='anyuser', password='anypwd')

    def test_delete_secret_confirmation(self):
        id_1 = uuid4().hex
        id_2 = uuid4().hex
        make('secret.Secret', id=id_1)
        s2 = make('secret.Secret', id=id_2)
        url = reverse('secret:delete-secret', kwargs={'pk': id_2})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'secret/delete-confirmation.html')
        self.assertEqual(resp.context['pk'], id_2)
        self.assertEqual(resp.context['username'], s2.username)

    def test_delete_secret(self):
        id_1 = uuid4().hex
        id_2 = uuid4().hex
        make('secret.Secret', id=id_1)
        make('secret.Secret', id=id_2)
        url = reverse('secret:delete-secret', kwargs={'pk': id_2})

        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Secret.objects.count(), 1)

    def test_login_required(self):
        self.client.logout()
        id_1 = uuid4().hex
        url = reverse('secret:delete-secret', kwargs={'pk': id_1})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
