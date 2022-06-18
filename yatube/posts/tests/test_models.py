from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст тестового поста, проверка теста',
        )

    def test_models_have_correct_name(self):
        '''Проверка __str__'''

    def test_models_have_correct_objects_name_post(self):
        '''Проверка str для поста'''
        post = PostModelTest.post
        act = post.__str__()
        self.assertEqual(act, PostModelTest.post.text[:15],
                         'Метод __str__ работает неправильно.')

    def test_models_have_correct_objects_name_group(self):
        '''Проверка str для группы'''
        group = PostModelTest.group
        act_group = group.__str__()
        self.assertEqual(act_group, PostModelTest.group.title,
                         'Метод __str__ работает неправильно.')

    def test_models_verbose_name_post(self):
        '''Проверка verbose_name'''
        post = PostModelTest.post
        verbose_names = {
            'text': 'Текст поста',
            'author': 'Автор',
            'pub_date': 'Дата создания',
            'group': 'Группа'}
        for field, verbose in verbose_names.items():
            with self.subTest(field=field):
                field_name = post._meta.get_field(field).verbose_name
                self.assertEqual(field_name, verbose)

    def test_models_help_text_post(self):
        '''Проверка help_text'''
        post = PostModelTest.post
        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'}
        for field, help_text in help_texts.items():
            with self.subTest(field=field):
                field_name = post._meta.get_field(field).help_text
                self.assertEqual(field_name, help_text)
