import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
            id=100
        )
        cls.group2 = Group.objects.create(
            title='Другая группа',
            slug='other',
            description='Тестовое описание',
            id=200
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id=502,
            group_id=100,
            image='posts/small.gif'
        )
        cls.post_author = Post.objects.create(
            author=cls.author,
            text='Тестовый пост автора',
            id=505,
            group_id=100)
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый текст комментария под постом',
            id=99,
            post_id=502)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_coorrect(self):
        '''Проверка шаблона'''
        templates = {reverse('posts:index'): 'posts/index.html',
                     reverse('posts:group_list', kwargs={
                         'slug': PostsPagesTests.group.slug}):
                             'posts/group_list.html',
                     reverse('posts:profile', kwargs={'username': 'auth'}):
                         'posts/profile.html',
                     reverse('posts:post_detail', kwargs={
                         'post_id': PostsPagesTests.post.id}):
                         'posts/post_detail.html',
                     reverse('posts:post_create'): 'posts/create_post.html',
                     reverse('posts:post_edit', kwargs={
                         'post_id': PostsPagesTests.post.id}):
                         'posts/create_post.html'}
        for reverse_name, template in templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_correct_context_list(self):
        '''Проверка контекста  со списками'''

        views = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': PostsPagesTests.group.slug}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for view in views:
            with self.subTest(view=view):
                response = self.authorized_client.get(view)
                first_obj = response.context['page_obj'][0]
                post_text_0 = first_obj.text
                post_author_0 = first_obj.author.username
                post_id_0 = first_obj.id
                post_image_0 = first_obj.image
                self.assertEqual(post_text_0, PostsPagesTests.post.text)
                self.assertEqual(post_author_0, 'auth')
                self.assertEqual(post_id_0, PostsPagesTests.post.id)
                self.assertEqual(post_image_0, 'posts/small.gif')

    def test_correct_context_detail_obj(self):
        '''Проверка контекста одного поста'''
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': PostsPagesTests.post.id})))
        self.assertEqual(response.context.get('post_d').text,
                         PostsPagesTests.post.text)
        self.assertEqual(
            response.context.get('post_d').author.username, 'auth')
        self.assertEqual(response.context.get('post_d').id,
                         PostsPagesTests.post.id)
        self.assertEqual(response.context.get('post_d').image,
                         PostsPagesTests.post.image)
        self.assertEqual(response.context['comments'][0].text,
                         PostsPagesTests.comment.text)

    def test_correct_context_form(self):
        '''Проверка контекста форм'''
        views = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={
                'post_id': PostsPagesTests.post.id})
        ]
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField,
                       'image': forms.fields.ImageField}
        for view in views:
            response = self.authorized_client.get(view)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(field, expected)

    def test_post_with_gpoup_not_in_page(self):
        '''Проверка, пост с группой не отображается на странице иной группы'''
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostsPagesTests.group2.slug}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_post_follow(self):
        '''Авторизованный пользователь может подписаться на автора'''
        response = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': PostsPagesTests.author.username}))
        response2 = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': PostsPagesTests.user.username}))
        self.assertTrue(Follow.objects.filter(
            author_id=PostsPagesTests.author.id,
            user_id=PostsPagesTests.user.id
        ).exists())
        self.assertFalse(Follow.objects.filter(
            author_id=PostsPagesTests.user.id,
            user_id=PostsPagesTests.user.id
        ).exists())
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'author'}))
        self.assertRedirects(response2, reverse(
            'posts:profile', kwargs={'username': 'auth'}))

    def test_post_unfollow(self):
        '''Авторизованный пользователь может отписаться от автора'''
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': PostsPagesTests.author.username}))
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': PostsPagesTests.author.username}))
        self.assertFalse(Follow.objects.filter(
            author_id=PostsPagesTests.author.id,
            user_id=PostsPagesTests.user.id
        ).exists())
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'author'}))

    def test_guest_client_follow(self):
        '''Неавторизованный пользователь не может подписаться на автора'''
        response = self.guest_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': PostsPagesTests.author.username}))
        self.assertRedirects(
            response,
            '/auth/login/?next=/profile/author/follow/')

    def test_follow_index(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': PostsPagesTests.author.username}))
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        first_obj = response.context['page_obj'][0]
        post_text_0 = first_obj.text
        post_author_0 = first_obj.author.username
        post_id_0 = first_obj.id
        self.assertEqual(post_text_0, PostsPagesTests.post_author.text)
        self.assertEqual(post_author_0, PostsPagesTests.author.username)
        self.assertEqual(post_id_0, PostsPagesTests.post_author.id)
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': PostsPagesTests.author.username}))
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='noname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests',
            id=100,
            description='Тестовое описание')
        for i in range(600, 612):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост',
                id=i,
                group_id=100
            )

    def setUp(self):
        self.user = User.objects.get(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_ten(self):
        '''Проверка количества постов на первой странице'''
        views = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                    'slug': PaginatorViewTest.group.slug}),
            reverse('posts:profile', kwargs={'username': 'noname'}),
        ]
        for view in views:
            resp = self.client.get(view)
            self.assertEqual(len(resp.context['page_obj']), 10)

    def test_last_page(self):
        '''Проверка количества постов на последней странице'''
        views = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': PaginatorViewTest.group.slug}),
            reverse('posts:profile', kwargs={'username': 'noname'}),
        ]
        for view in views:
            resp = self.client.get(view + '?page=2')
            self.assertEqual(len(resp.context['page_obj']), 2)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='new')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testscache',
            id=250,
            description='Тестовое описание')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id=600,
            group_id=250
        )

    def setUp(self):
        self.user = User.objects.get(username='new')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_content_cache(self):
        '''Проверка кэша на главной странице'''
        response = self.authorized_client.get(reverse('posts:index'))
        self.post.delete()
        new_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, new_response.content)
        cache.clear()

        last_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotIn(self.post, last_response.context.get('page_obj'))
