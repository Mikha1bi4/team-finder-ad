# tests/test_integration.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import json

from projects.models import Project
from users.models import Skill

User = get_user_model()


class IntegrationTest(TestCase):
    """Integration tests for the entire application"""

    def setUp(self):
        self.client = Client()

        # Create test image for avatar
        image = Image.new('RGB', (100, 100), color='red')
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        self.avatar = SimpleUploadedFile('avatar.png', image_bytes.getvalue(), content_type='image/png')

        # Create users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='pass123',
        )

        self.user2 = User.objects.create_user(
            email='user2@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='pass123',
        )

        # Create skills
        self.skill_python = Skill.objects.create(name='Python')
        self.skill_django = Skill.objects.create(name='Django')
        self.skill_js = Skill.objects.create(name='JavaScript')

        # Create project
        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.user1,
            status='open'
        )
        self.project.participants.add(self.user1)

    def test_complete_user_journey_favorites(self):
        """Test complete user journey for Favorites functionality"""
        # Login - используем URL из users app
        response = self.client.post('/users/login/', {
            'username': 'user1@example.com',
            'password': 'pass123'
        })
        # Редирект на projects:list
        self.assertRedirects(response, '/projects/list/')

        # View project list
        response = self.client.get('/projects/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_list.html')

        # Add project to favorites
        response = self.client.post(f'/projects/{self.project.id}/toggle-favorite/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['favorited'], 'Избранный')

        # View favorites
        response = self.client.get('/projects/favorites/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project_list'].count(), 1)

        # View user details
        response = self.client.get(f'/users/{self.user1.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user1)

    def test_complete_user_journey_user_skills(self):
        """Test complete user journey for User Skills"""
        # Login as user1
        self.client.force_login(self.user1)

        # Add skill to user1
        response = self.client.post(
            f'/users/{self.user1.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill_python.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['added'])
        self.user1.refresh_from_db()
        self.assertIn(self.skill_python, self.user1.skills.all())

        # Login as user2 and add skill
        self.client.force_login(self.user2)
        response = self.client.post(
            f'/users/{self.user2.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill_django.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.user2.refresh_from_db()
        self.assertIn(self.skill_django, self.user2.skills.all())

        # Filter users by skill
        response = self.client.get('/users/list/?skill=Python')
        self.assertEqual(response.status_code, 200)
        users = response.context['user_list']
        self.assertEqual(users.count(), 1)
        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)

    def test_complete_user_journey_project_skills(self):
        """Test complete user journey for Project Skills"""
        # Login as project owner
        self.client.force_login(self.user1)

        # Add skill to project
        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill_python.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['added'])
        self.project.refresh_from_db()
        self.assertIn(self.skill_python, self.project.skills.all())

        # View project details
        response = self.client.get(f'/projects/{self.project.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)

        # Filter projects by skill
        response = self.client.get('/projects/list/?skill=Python')
        self.assertEqual(response.status_code, 200)
        projects = response.context['project_list']
        self.assertEqual(projects.count(), 1)
        self.assertIn(self.project, projects)

        # Remove skill from project
        response = self.client.post(
            f'/projects/{self.project.id}/skills/{self.skill_python.id}/remove/'
        )
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertNotIn(self.skill_python, self.project.skills.all())

    def test_project_completion_flow(self):
        """Test project completion flow"""
        # Login as project owner
        self.client.force_login(self.user1)

        # Complete project
        response = self.client.post(f'/projects/{self.project.id}/complete/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'closed')

        # Try to complete again (should fail)
        response = self.client.post(f'/projects/{self.project.id}/complete/')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Проект уже завершен')

    def test_participation_flow(self):
        """Test participation flow"""
        # Login as user2
        self.client.force_login(self.user2)

        # Join project
        response = self.client.post(f'/projects/{self.project.id}/toggle-participate/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['message'], 'Вы присоединились к проекту')
        self.project.refresh_from_db()
        self.assertIn(self.user2, self.project.participants.all())

        # Leave project
        response = self.client.post(f'/projects/{self.project.id}/toggle-participate/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Вы вышли из проекта')
        self.project.refresh_from_db()
        self.assertNotIn(self.user2, self.project.participants.all())

    def test_skill_autocomplete_flow(self):
        """Test skill autocomplete flow"""
        # Test user skills autocomplete
        response = self.client.get('/users/skills/?q=Py')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Python')

        # Test user skills autocomplete with different query
        response = self.client.get('/users/skills/?q=Ja')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'JavaScript')

    def test_profile_edit_flow(self):
        """Test profile edit flow"""
        # Login as user1
        self.client.force_login(self.user1)

        # Edit profile
        response = self.client.post('/users/edit-profile/', {
            'name': 'Johnathan',
            'surname': 'Doe',
            'phone': '+71234567890',
            'about': 'Updated about text',
            'github_url': 'https://github.com/johndoe'
        })
        self.assertRedirects(response, f'/users/{self.user1.id}/')

        # Verify changes
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.name, 'Johnathan')
        self.assertEqual(self.user1.about, 'Updated about text')
        self.assertEqual(self.user1.github_url, 'https://github.com/johndoe')

    def test_password_change_flow(self):
        """Test password change flow"""
        # Login as user1
        self.client.force_login(self.user1)

        # Change password
        response = self.client.post('/users/change-password/', {
            'old_password': 'pass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })
        self.assertRedirects(response, f'/users/{self.user1.id}/')

        # Verify password was changed
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password('newpass456'))

        # Logout and login with new password
        self.client.logout()
        response = self.client.post('/users/login/', {
            'username': 'user1@example.com',
            'password': 'newpass456'
        })
        self.assertRedirects(response, '/projects/list/')

    def test_project_edit_flow(self):
        """Test project edit flow"""
        # Login as project owner
        self.client.force_login(self.user1)

        # Edit project - используем правильный URL
        response = self.client.post(f'/projects/{self.project.id}/edit/', {
            'name': 'Updated Project Name',
            'description': 'Updated description',
            'github_url': 'https://github.com/test/updated',
            'status': 'open'
        })
        self.assertRedirects(response, f'/projects/{self.project.id}/')

        # Verify changes
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project Name')
        self.assertEqual(self.project.description, 'Updated description')
        self.assertEqual(self.project.github_url, 'https://github.com/test/updated')


class PermissionTest(TestCase):
    """Tests for permission handling"""

    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(
            email='owner@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='pass123',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='pass123',
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.owner,
            status='open'
        )

        self.skill = Skill.objects.create(name='Python')

    def test_owner_can_edit_project(self):
        """Test project owner can edit project"""
        self.client.force_login(self.owner)
        response = self.client.get(f'/projects/{self.project.id}/edit/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f'/projects/{self.project.id}/edit/', {
            'name': 'Updated Name',
            'description': 'Updated description',
            'github_url': 'https://github.com/test/updated',
            'status': 'open'
        })
        self.assertEqual(response.status_code, 302)

    def test_non_owner_cannot_edit_project(self):
        """Test non-owner cannot edit project"""
        self.client.force_login(self.other_user)
        response = self.client.get(f'/projects/{self.project.id}/edit/')
        self.assertEqual(response.status_code, 403)

    def test_owner_can_manage_project_skills(self):
        """Test project owner can manage skills"""
        self.client.force_login(self.owner)

        # Add skill
        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['added'])

        # Remove skill
        self.project.skills.add(self.skill)
        response = self.client.post(
            f'/projects/{self.project.id}/skills/{self.skill.id}/remove/'
        )
        self.assertEqual(response.status_code, 200)

    def test_non_owner_cannot_manage_project_skills(self):
        """Test non-owner cannot manage skills"""
        self.client.force_login(self.other_user)

        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Отказано в доступе')

    def test_owner_can_complete_project(self):
        """Test project owner can complete project"""
        self.client.force_login(self.owner)
        response = self.client.post(f'/projects/{self.project.id}/complete/')
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'closed')

    def test_non_owner_cannot_complete_project(self):
        """Test non-owner cannot complete project"""
        self.client.force_login(self.other_user)
        response = self.client.post(f'/projects/{self.project.id}/complete/')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Нет прав')

    def test_owner_can_edit_own_profile(self):
        """Test user can edit own profile"""
        self.client.force_login(self.owner)
        response = self.client.get('/users/edit-profile/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/users/edit-profile/', {
            'name': 'Updated Name',
            'surname': 'Updated Surname',
            'phone': '+71234567890',
            'about': 'Updated about',
            'github_url': 'https://github.com/updated'
        })
        self.assertEqual(response.status_code, 302)

    def test_user_can_manage_own_skills(self):
        """Test user can manage own skills"""
        self.client.force_login(self.owner)

        # Add skill
        response = self.client.post(
            f'/users/{self.owner.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['added'])

        # Remove skill
        self.owner.skills.add(self.skill)
        response = self.client.post(
            f'/users/{self.owner.id}/skills/{self.skill.id}/remove/'
        )
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_manage_other_skills(self):
        """Test user cannot manage other's skills"""
        self.client.force_login(self.other_user)

        response = self.client.post(
            f'/users/{self.owner.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Отказано в доступе')

    def test_unauthenticated_redirects(self):
        """Test unauthenticated users are redirected"""
        # Try to access protected pages
        protected_pages = [
            '/projects/create-project/',
            '/projects/favorites/',
            '/users/edit-profile/',
            '/users/change-password/'
        ]

        for page in protected_pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 302)  # Redirect to login
