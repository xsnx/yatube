from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, User, Group


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
        self.assertRedirects(response, '/auth/login/?next=/new/',
                             status_code=302, target_status_code=200,
                             msg_prefix='', fetch_redirect_response=True)
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

    def test_views_post(self):
        for url in self.url_post:
            response = self.auth_client.get(url)
            self.assertContains(response, self.post.text, count=1)

    def test_views_edit_post(self):
        self.post.text = 'Test edit post'
        self.post.save()
        for url in self.url_post:
            response = self.auth_client.get(url)
            self.assertContains(response, 'Test edit post', count=1)


class Test_page_404_500(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_page_404(self):
        response = self.client.get('/page/404')
        self.assertEqual(response.status_code, 301)


class Test_post_image(TestCase):
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

    def test_image_new(self):
        with open('posts/testfile/test.jpg', 'rb') as img:
            response = self.client.post(reverse('new_post'),
                                        data={'author': self.user,
                                              'text': 'post with image',
                                              'image': img}, follow=True)
        self.assertRedirects(response, '/')
        self.assertContains(response, '<img class="card-img"')

    def test_image_edit(self):
        self.client.post(reverse('new_post'),
                         data={'author': self.user,
                               'post_id': 1,
                               'text': 'post image'},
                         follow=True)
        with open('posts/testfile/test.jpg', 'rb') as img:
            response = self.client.post(
                reverse('post_edit', kwargs={'username': self.user,
                                             'post_id': 1}),
                data={'text': 'Test with image',
                      'group': self.group.id,
                      'image': img},
                follow=True)

            self.assertRedirects(response, '/TestUser/1/')
            self.assertContains(response, '<img class="card-img"')
            resp = self.client.get('/group/group/')
            self.assertContains(resp, '<img class="card-img"')

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


