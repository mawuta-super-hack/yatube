from http import HTTPStatus
from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id=500
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exist(self):
        '''Проверка сущестования страниц'''
        HTTP200 = HTTPStatus.OK
        url_list = [
            '/',
            '/group/test/',
            '/posts/500/',
            '/profile/auth/'
        ]
        for url in url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTP200)

        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTP200)

        response = self.authorized_client.get('/posts/500/edit/')
        self.assertEqual(response.status_code, HTTP200)

        response = self.guest_client.get('/unexsisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_templates(self):
        '''Проверка шаблона'''

        templates = {'/': 'posts/index.html',
                     '/group/test/': 'posts/group_list.html',
                     '/profile/auth/': 'posts/profile.html',
                     '/posts/500/': 'posts/post_detail.html',
                     '/create/': 'posts/create_post.html',
                     '/posts/500/edit/': 'posts/create_post.html'}
        for url, template in templates.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
