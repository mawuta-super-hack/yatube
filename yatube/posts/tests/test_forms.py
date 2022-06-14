import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post, User
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA_ROOT,
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }})
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
            id=100
        )
        cls.new_group = Group.objects.create(
            title='Тестовая группа2',
            slug='tests',
            description='Тестовое описание',
            id=101
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id=500,
            group_id=100
        )

        cls.form = PostForm()
        cls.comment_form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_form(self):
        '''Форма создает запись в БД'''
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        form_data = {'text': 'Тестирование формы',
                     'group': PostsFormTests.group.id,
                     'image': uploaded}
        resp = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(resp, reverse(
            'posts:profile', kwargs={'username': 'auth'}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестирование формы',
                group=PostsFormTests.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_form(self):
        '''Форма редактирует запись в БД'''
        post_count = Post.objects.count()
        form_data = {'text': 'Тестирование формы',
                     'group': PostsFormTests.new_group.id}
        resp = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostsFormTests.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(resp, reverse(
            'posts:post_detail', kwargs={'post_id': PostsFormTests.post.id}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестирование формы',
                group=PostsFormTests.new_group.id,
            ).exists()
        )
        self.assertEqual(len(self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostsFormTests.group.slug})).context['page_obj']), 0)

    def test_create_form_guest(self):
        '''Проверка: неавторизованный пользователь
        не может создавать пост
        '''
        response = self.guest_client.get(
            reverse('posts:post_create'))
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_edit_form_guest(self):
        '''Проверка: неавторизованный пользователь
        не может редактировать пост
        '''
        response = self.guest_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': PostsFormTests.post.id}))
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostsFormTests.post.id}/edit/')

    def test_comment_form(self):
        '''Форма создает комментарий под постом'''
        comment_count = Comment.objects.count()
        form_data = {'text': 'Тестирование формы комментария'}
        resp = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': PostsFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(resp, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsFormTests.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестирование формы комментария').exists()
        )

    def test_create_comment(self):
        '''Проверка: неавторизованный пользователь
        не может оставлять комментарий
            '''
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={
                'post_id': PostsFormTests.post.id}))
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostsFormTests.post.id}/comment/')
