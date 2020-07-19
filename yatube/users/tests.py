from django.test import Client, TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class TestProfile(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username='TestUser',
            email='test@user.com',
            password='12345'
        )

    def test_login_profile(self):
        response = self.client.post("/auth/login/",
                                    {'username': 'TestUser',
                                     'password': '12345'},
                                    follow=True
                                    )
        self.assertEqual(response.status_code, 200)

    def test_page_profile(self):
        self.client.force_login(user=self.user)
        response = self.client.get("/TestUser", follow=True)
        self.assertEqual(response.status_code, 200)
