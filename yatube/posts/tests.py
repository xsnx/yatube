import io

from PIL import Image
from django.core.files.base import ContentFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, User, Group, Comment, Follow
import tempfile
from django.core.cache import cache


# CASH = {'default': {
#     'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
# }}
# @override_settings(CACHES=CASH)
class TestGroups(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.group = Group.objects.create(
            title='testgroup',
            slug='testgroup',
            description='test group'
        )

    def test_page_not_found(self):
        response = self.client.get('/groups/not_exist/')
        self.assertEqual(response.status_code, 404)

    def test_exists_group(self):
        response = self.client.get('/group/testgroup/')
        self.assertEqual(response.status_code, 200)


class TestPost(TestCase):
    def setUp(self) -> None:
        self.non_auth_client = Client()
        self.auth_client = Client()
        self.user = User.objects.create_user(
            username='TestUser',
            email='test@user.com',
            password='12345'
        )
        self.auth_client.force_login(user=self.user)

    def test_create_post_unlogin(self):
        response = self.non_auth_client.post(
            reverse('new_post'),
            data={'text': 'Test post'},
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/new/')
        self.assertEqual(Post.objects.count(), 0)

    def test_create_post_login(self):
        response = self.auth_client.post(
            reverse('new_post'),
            data={'text': 'Test post'},
            follow=True
        )
        self.assertRedirects(response, '/')
        self.assertEqual(Post.objects.count(), 1)

    def test_edit_post(self):
        self.auth_client.post(
            reverse('new_post'),
            data={'text': 'Test post', 'post_id': 1},
            follow=True
        )
        response = self.auth_client.post(
            reverse('post_edit',
                    kwargs={'username': 'TestUser', 'post_id': 1}),
            data={'text': 'Test edit post'},
            follow=True
        )
        self.assertRedirects(response, '/TestUser/1/')
        self.assertEqual(Post.objects.count(), 1)


class TestPostViews(TestCase):
    def setUp(self) -> None:
        self.auth_client = Client()
        self.user = User.objects.create_user(
            username='TestUser',
            email='test@user.com',
            password='12345'
        )
        self.auth_client.force_login(self.user)
        self.group = Group.objects.create(
            title='group',
            slug='group',
            description='test group'
        )
        self.post = Post.objects.create(
            text='Test post',
            group=self.group,
            author=self.user
        )
        self.url_post = {
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('group', kwargs={'slug': self.group.slug}),
            reverse('post', kwargs={'username': self.user.username,
                                    'post_id': self.post.id})
        }
        cache.clear()

    def test_views_post(self):
        for url in self.url_post:
            cache.clear()
            response = self.auth_client.get(url)
            self.assertContains(response, self.post.text, count=1)

    #@override_settings(CACHES=CASH)
    def test_views_edit_post(self):
        self.post.text = 'Test edit post'
        self.post.save()
        for url in self.url_post:
            response = self.auth_client.get(url)
            self.assertContains(response, 'Test edit post', count=1)


class TestPage404and500(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_page_404(self):
        response = self.client.get('/non_test_page/404')
        self.assertEqual(response.status_code, 301)


class TestPostImage(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='TestUser',
            email='test@user.com',
            password='12345'
        )
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            title='group',
            slug='group',
            description='test group'
        )
        cache.clear()

    #@override_settings(CACHES=CASH)
    def test_image_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                byte_image = io.BytesIO()
                im = Image.new("RGB", size=(500, 500), color=(255, 255, 0, 0))
                im.save(byte_image, format='png')
                byte_image.seek(0)
                response = self.client.post(reverse('new_post'),
                                            data={'text': 'post with imag',
                                                  'image': ContentFile(
                                                      byte_image.read(),
                                                      name='test.png')},
                                            follow=True)
                self.assertRedirects(response, '/')
                self.assertEqual(Post.objects.count(), 1)
                self.assertContains(response, '<img')

    def test_image_edit(self):
        self.client.post(reverse('new_post'),
                         data={'author': self.user,
                               'post_id': 1,
                               'text': 'post image'},
                         follow=True)
        with tempfile.TemporaryDirectory() as temp_directory:
            with override_settings(MEDIA_ROOT=temp_directory):
                byte_image = io.BytesIO()
                im = Image.new("RGB", size=(500, 500), color=(255, 0, 0, 0))
                im.save(byte_image, format='jpeg')
                byte_image.seek(0)
                params = {'username': self.user.username, 'post_id': 1}
                payload = {'text': 'post with image',
                           'image': ContentFile(byte_image.read(),
                                                name='test.jpeg')}
                response = self.client.post(
                    reverse('post_edit', kwargs=params), data=payload,
                    follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<img')

    def test_non_image_new(self):
        try:
            with open('posts/testfile/test.7z', 'rb') as img:
                self.client.post(reverse('new_post'),
                                 data={'author': self.user,
                                       'text': 'post with image',
                                       'image': img}, follow=True)
        except IOError:
            print('IOError has occurred!')

    def test_non_image_post_edit(self):
        self.client.post(reverse('new_post'),
                         data={'author': self.user,
                               'post_id': 1,
                               'text': 'post image'},
                         follow=True)
        try:
            with open('posts/testfile/test.7z', 'rb') as img:
                self.client.post(
                    reverse('post_edit', kwargs={'username': self.user,
                                                 'post_id': 1}),
                    data={'text': 'Test with image',
                          'group': self.group.id,
                          'image': img},
                    follow=True)
        except IOError:
            print('IOError has occurred!')


class TestAddComment(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='TestUser',
            email='test@user.com',
            password='12345'
        )
        self.group = Group.objects.create(
            title='group',
            slug='group',
            description='test group'
        )
        self.post = Post.objects.create(
            text='Test post',
            group=self.group,
            author=self.user
        )

    def test_comment(self):
        self.client.force_login(self.user)
        params = {'username': self.user, 'post_id': self.post.id}
        date = {'text': 'test comment'}
        response = self.client.post(
            reverse('add_comment', kwargs=params), data=date,
            follow=True)

        self.assertRedirects(response, f'/{self.user}/{self.post.id}/')
        self.assertEqual(Comment.objects.count(), 1)
        self.assertContains(response, 'test comment')

    def test_comment_unlogin(self):
        params = {'username': self.user, 'post_id': self.post.id}
        date = {'text': 'test comment'}
        response = self.client.post(
            reverse('add_comment', kwargs=params), data=date,
            follow=True)
        self.assertRedirects(response, '/auth/login/?next=%2FTestUser%2F1'
                                       '%2Fcomment%2F')
        self.assertEqual(Comment.objects.count(), 0)


class TestCache(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='TestUser',
            email='test@user.com',
            password='12345'
        )
        self.group = Group.objects.create(
            title='group',
            slug='group',
            description='test group'
        )
        self.post = Post.objects.create(
            text='Test post',
            group=self.group,
            author=self.user
        )

    def test_cache_index(self):
        self.client.force_login(self.user)
        self.client.get(reverse('index'))
        response = self.client.post(
            reverse('new_post'),
            data={'text': 'test_cache_index'},
            follow=True
        )
        self.assertRedirects(response, '/')
        self.assertEqual(Post.objects.count(), 2)
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Test post')
        self.assertNotContains(response, 'test_cache_index')
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'test_cache_index')


class TestFollow(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='TestUser1',
            email='test1@user.com',
            password='12345'
        )
        self.user2 = User.objects.create_user(
            username='TestUser2',
            email='test2@user.com',
            password='12345'
        )
        self.group = Group.objects.create(
            title='group',
            slug='group',
            description='test group'
        )
        self.post = Post.objects.create(
            text='Test post',
            group=self.group,
            author=self.user1
        )
        self.post = Post.objects.create(
            text='test_follow_index',
            group=self.group,
            author=self.user2
        )

    def test_profile_follow(self):
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("profile_follow", args=[self.user2]))
        self.assertRedirects(response, f'/{self.user2}/')
        self.assertEqual(Follow.objects.count(), 1)

    def test_profile_unfollow(self):
        self.client.force_login(self.user1)
        self.client.get(
            reverse("profile_follow", args=[self.user2]))
        response = self.client.get(
            reverse("profile_unfollow", args=[self.user2]))
        self.assertRedirects(response, f'/{self.user2}/')
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_index(self):
        self.client.force_login(self.user1)
        self.client.get(
            reverse("profile_follow", args=[self.user2]))
        response = self.client.get(reverse('follow_index'), follow=True)
        self.assertContains(response, 'test_follow_index')
        self.assertNotContains(response, 'Test post')
