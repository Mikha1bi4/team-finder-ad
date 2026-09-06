# tests/test_urls.py
from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class URLTests(TestCase):
    """Tests for URL configuration"""

    def test_root_url(self):
        """Test root URL resolves to project_list"""
        url = reverse('home')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'RedirectView')

    def test_project_list_url(self):
        """Test project list URL"""
        url = reverse('projects:list')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'ProjectListView')

    def test_project_details_url(self):
        """Test project details URL"""
        url = reverse('projects:detail', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'ProjectDetailView')

    def test_create_project_url(self):
        """Test create project URL"""
        url = reverse('projects:create-project')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'ProjectCreateView')

    def test_edit_project_url(self):
        """Test edit project URL"""
        url = reverse('projects:edit', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'ProjectUpdateView')

    def test_toggle_favorite_url(self):
        """Test toggle favorite URL"""
        url = reverse('projects:toggle-favorite', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'toggle_favorite')

    def test_favorites_url(self):
        """Test favorites URL"""
        url = reverse('projects:favorites')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'FavoritesProjectsListView')

    def test_complete_project_url(self):
        """Test complete project URL"""
        url = reverse('projects:complete', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'complete_project')

    def test_toggle_participate_url(self):
        """Test toggle participate URL"""
        url = reverse('projects:toggle-participate', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'toggle_participate')

    def test_project_skill_autocomplete_url(self):
        """Test project skill autocomplete URL"""
        url = reverse('projects:get_skills')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'get_skills')

    def test_add_project_skill_url(self):
        """Test add project skill URL"""
        url = reverse('projects:add_skill', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'add_skill')

    def test_remove_project_skill_url(self):
        """Test remove project skill URL"""
        url = reverse('projects:remove_skill', args=[1, 1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'remove_skill')

    def test_user_list_url(self):
        """Test user list URL"""
        url = reverse('users:list')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'UserListView')

    def test_user_details_url(self):
        """Test user details URL"""
        url = reverse('users:detail', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'UserDetailView')

    def test_register_url(self):
        """Test register URL"""
        url = reverse('users:register')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'CreateView')

    def test_login_url(self):
        """Test login URL"""
        url = reverse('users:login')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'LoginView')

    def test_logout_url(self):
        """Test logout URL"""
        url = reverse('users:logout')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'LogoutView')

    def test_edit_profile_url(self):
        """Test edit profile URL"""
        url = reverse('users:edit-profile')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'UserUpdateView')

    def test_change_password_url(self):
        """Test change password URL"""
        url = reverse('users:change-password')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class.__name__, 'UserPasswordChangeView')

    def test_user_skill_autocomplete_url(self):
        """Test user skill autocomplete URL"""
        url = reverse('users:get_skills')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'get_skills')

    def test_add_user_skill_url(self):
        """Test add user skill URL"""
        url = reverse('users:add_skill', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'add_skill')

    def test_remove_user_skill_url(self):
        """Test remove user skill URL"""
        url = reverse('users:remove_skill', args=[1, 1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, 'remove_skill')


class AuthenticationURLTests(TestCase):
    """Tests for authentication URLs"""

    def test_register_url_accessible(self):
        """Test register URL is accessible"""
        response = self.client.get('/users/register/')
        self.assertEqual(response.status_code, 200)

    def test_login_url_accessible(self):
        """Test login URL is accessible"""
        response = self.client.get('/users/login/')
        self.assertEqual(response.status_code, 200)

    def test_logout_requires_authentication_and_post(self):
        """Test logout requires authentication and POST method"""
        # GET запрос без аутентификации должен вернуть 405 (Method Not Allowed)
        response = self.client.get('/users/logout/')
        self.assertEqual(response.status_code, 405)  # LogoutView требует POST

        # POST запрос без аутентификации должен редиректить на login
        response = self.client.post('/users/logout/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_logout_with_authenticated_user(self):
        """Test logout with authenticated user"""
        # Создаем и логиним пользователя
        user = User.objects.create_user(
            email='test@example.com',
            name='Test',
            surname='User',
            phone='+71234567890',
            password='testpass123'
        )
        self.client.force_login(user)

        # POST запрос должен разлогинить и перенаправить
        response = self.client.post('/users/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/users/login/')

    def test_skills_url_accessible(self):
        """Test skills autocomplete URL is accessible"""
        response = self.client.get('/users/skills/?q=python')
        self.assertEqual(response.status_code, 200)


class RedirectTests(TestCase):
    """Tests for redirects"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png', b'content', content_type='image/png')
        )

    def test_root_redirects_to_project_list(self):
        """Test root redirects to project list"""
        response = self.client.get('/')
        self.assertRedirects(response, '/projects/list/')

    def test_login_redirects_to_project_list(self):
        """Test successful login redirects to project list"""
        response = self.client.post('/users/login/', {
            'username': 'test@example.com',  # Важно: в LoginView используется username
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/projects/list/')

    def test_register_redirects_to_project_list(self):
        """Test successful registration redirects to project list"""

        response = self.client.post('/users/register/', {
            'email': 'newuser@example.com',
            'name': 'New',
            'surname': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        })
        self.assertRedirects(response, '/projects/list/')

    def test_create_project_redirects_to_project_page(self):
        """Test successful project creation redirects to project page"""
        self.client.force_login(self.user)

        response = self.client.post('/projects/create-project/', {
            'name': 'New Project',
            'description': 'Test description',
            'github_url': 'https://github.com/test/project',
            'status': 'open'
        })

        # Should redirect to the new project's page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/projects/'))

    def test_edit_profile_redirects_to_user_page(self):
        """Test successful profile edit redirects to user page"""
        self.client.force_login(self.user)

        response = self.client.post('/users/edit-profile/', {
            'name': 'John',
            'surname': 'Doe',
            'phone': '+71234567890',
            'about': 'Updated about text',
            'github_url': 'https://github.com/johndoe'
        })

        self.assertRedirects(response, f'/users/{self.user.id}/')

    def test_change_password_redirects_to_user_page(self):
        """Test successful password change redirects to user page"""
        self.client.force_login(self.user)

        response = self.client.post('/users/change-password/', {
            'old_password': 'testpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        })

        self.assertRedirects(response, f'/users/{self.user.id}/')

    def test_logout_redirects_to_login(self):
        """Test logout redirects to login page"""
        self.client.force_login(self.user)
        response = self.client.post('/users/logout/')
        self.assertRedirects(response, '/users/login/')


class StatusCodeTests(TestCase):
    """Tests for HTTP status codes"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123'
        )

    def test_project_list_status_code(self):
        """Test project list returns 200"""
        response = self.client.get('/projects/list/')
        self.assertEqual(response.status_code, 200)

    def test_user_list_status_code(self):
        """Test user list returns 200"""
        response = self.client.get('/users/list/')
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_requires_login(self):
        """Test edit profile redirects if not logged in"""
        response = self.client.post('/users/edit-profile/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_change_password_requires_login(self):
        """Test change password redirects if not logged in"""
        response = self.client.post('/users/change-password/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_create_project_requires_login(self):
        """Test create project redirects if not logged in"""
        response = self.client.post('/projects/create-project/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))
