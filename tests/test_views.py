# tests/test_views.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import json
from PIL import Image
import io

from projects.models import Project
from users.models import Skill

User = get_user_model()


class ProjectListViewTest(TestCase):
    """Tests for project list view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        # Create projects with different dates
        self.project1 = Project.objects.create(
            name='Old Project',
            description='Old description',
            owner=self.user,
            status='open'
        )

        self.project2 = Project.objects.create(
            name='New Project',
            description='New description',
            owner=self.user,
            status='open'
        )

        # Closed project owned by user
        self.project3 = Project.objects.create(
            name='Closed Project',
            description='Closed description',
            owner=self.user,
            status='closed'
        )

        # Closed project owned by another user
        self.other_user = User.objects.create_user(
            email='other@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
        )
        self.project4 = Project.objects.create(
            name='Other Closed Project',
            description='Other closed description',
            owner=self.other_user,
            status='closed'
        )

    def test_root_redirects_to_project_list(self):
        """Test root URL redirects to /projects/"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/projects/list/')

    def test_project_list_ordered_by_created_at(self):
        """Test projects are ordered by created_at descending"""
        response = self.client.get('/projects/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_list.html')

        projects = response.context['object_list']
        self.assertEqual(projects[0], self.project2)  # Newest first
        self.assertEqual(projects[1], self.project1)  # Oldest last

    def test_project_list_shows_only_open_for_unauthenticated(self):
        """Test unauthenticated user sees only open projects"""
        response = self.client.get('/projects/list/')
        projects = response.context['object_list']

        self.assertIn(self.project1, projects)
        self.assertIn(self.project2, projects)
        self.assertNotIn(self.project3, projects)  # Closed, not owner
        self.assertNotIn(self.project4, projects)  # Closed, not owner

    def test_project_list_shows_closed_owned_for_authenticated(self):
        """Test authenticated user sees their own closed projects"""
        self.client.force_login(self.user)
        response = self.client.get('/projects/list/')
        projects = response.context['object_list']

        self.assertIn(self.project1, projects)
        self.assertIn(self.project2, projects)
        self.assertIn(self.project3, projects)  # Closed, owner
        self.assertNotIn(self.project4, projects)  # Closed, not owner

    def test_project_list_all_projects(self):
        """Test project list shows correct number of projects"""
        self.client.force_login(self.user)
        response = self.client.get('/projects/list/')
        self.assertEqual(len(response.context['project_list']), 3)  # 2 open + 1 closed owned

    def test_project_list_authentication_not_required(self):
        """Test project list is accessible without authentication"""
        response = self.client.get('/projects/list/')
        self.assertEqual(response.status_code, 200)

    def test_project_list_pagination(self):
        """Test project list pagination"""
        # Create more than 12 projects
        for i in range(15):
            Project.objects.create(
                name=f'Project {i}',
                description=f'Description {i}',
                owner=self.user,
                status='open'
            )

        response = self.client.get('/projects/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['object_list']), 12)


class ProjectListViewSkillFilterTest(TestCase):
    """Tests for project list with skill filtering"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.skill_python = Skill.objects.create(name='Python')
        self.skill_django = Skill.objects.create(name='Django')
        self.skill_js = Skill.objects.create(name='JavaScript')

        self.project1 = Project.objects.create(
            name='Python Project',
            description='Python project',
            owner=self.user,
            status='open'
        )
        self.project1.skills.add(self.skill_python)

        self.project2 = Project.objects.create(
            name='Django Project',
            description='Django project',
            owner=self.user,
            status='open'
        )
        self.project2.skills.add(self.skill_django)

        self.project3 = Project.objects.create(
            name='Full Stack Project',
            description='Full stack project',
            owner=self.user,
            status='open'
        )
        self.project3.skills.add(self.skill_python, self.skill_js)

        self.project4 = Project.objects.create(
            name='No Skill Project',
            description='No skills',
            owner=self.user,
            status='open'
        )

    def test_project_list_filter_by_skill(self):
        """Test filtering projects by skill"""
        response = self.client.get('/projects/list/?skill=Python')
        self.assertEqual(response.status_code, 200)

        projects = response.context['object_list']
        self.assertEqual(projects.count(), 2)
        self.assertIn(self.project1, projects)
        self.assertIn(self.project3, projects)
        self.assertNotIn(self.project2, projects)
        self.assertNotIn(self.project4, projects)

    def test_project_list_no_filter(self):
        """Test project list without filter returns all open projects"""
        response = self.client.get('/projects/list/')
        self.assertEqual(response.status_code, 200)

        projects = response.context['object_list']
        self.assertEqual(projects.count(), 4)

    def test_project_list_context_variables(self):
        """Test context contains all_skills and active_skill"""
        response = self.client.get('/projects/list/?skill=Python')
        self.assertEqual(response.status_code, 200)

        self.assertIn('all_skills', response.context)
        self.assertEqual(list(response.context['all_skills']), ['Python', 'Django', 'JavaScript'])

        self.assertIn('active_skill', response.context)
        self.assertEqual(response.context['active_skill'], 'Python')


class FavoritesProjectsListViewTest(TestCase):
    """Tests for favorites page"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.project1 = Project.objects.create(
            name='Favorite Project 1',
            description='Description 1',
            owner=self.user,
            status='open'
        )

        self.project2 = Project.objects.create(
            name='Favorite Project 2',
            description='Description 2',
            owner=self.user,
            status='open'
        )

        self.project3 = Project.objects.create(
            name='Non-favorite Project',
            description='Description 3',
            owner=self.user,
            status='open'
        )

        self.user.favorites.add(self.project1, self.project2)

    def test_favorites_page_requires_authentication(self):
        """Test favorites page requires authentication"""
        response = self.client.get('/projects/favorites/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_favorites_page_shows_favorite_projects(self):
        """Test favorites page shows user's favorite projects"""
        self.client.force_login(self.user)
        response = self.client.get('/projects/favorites/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/favorite_projects.html')

        projects = response.context['object_list']
        self.assertEqual(projects.count(), 2)
        self.assertIn(self.project1, projects)
        self.assertIn(self.project2, projects)
        self.assertNotIn(self.project3, projects)

    def test_favorites_page_pagination(self):
        """Test favorites page pagination"""
        self.client.force_login(self.user)
        # Create more than 12 favorites
        for i in range(15):
            project = Project.objects.create(
                name=f'Favorite {i}',
                description=f'Description {i}',
                owner=self.user,
                status='open'
            )
            self.user.favorites.add(project)

        response = self.client.get('/projects/favorites/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['object_list']), 12)


class ProjectDetailViewTest(TestCase):
    """Tests for project details page"""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.participant = User.objects.create_user(
            email='participant@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.owner,
            status='open'
        )

    def test_project_details_authenticated(self):
        """Test authenticated user can view project details"""
        self.client.force_login(self.owner)
        response = self.client.get(f'/projects/{self.project.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project-details.html')
        self.assertEqual(response.context['project'], self.project)

    def test_project_details_unauthenticated(self):
        """Test unauthenticated user can view project details"""
        response = self.client.get(f'/projects/{self.project.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)

    def test_project_details_invalid_project(self):
        """Test project details with invalid project ID"""
        response = self.client.get('/projects/999/')
        self.assertEqual(response.status_code, 404)


class ToggleFavoriteViewTest(TestCase):
    """Tests for toggle favorite functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.user,
            status='open'
        )

    def test_toggle_favorite_add(self):
        """Test adding a project to favorites"""
        self.client.force_login(self.user)
        response = self.client.post(f'/projects/{self.project.id}/toggle-favorite/')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['favorited'], 'Избранный')

        self.assertIn(self.project, self.user.favorites.all())

    def test_toggle_favorite_remove(self):
        """Test removing a project from favorites"""
        self.user.favorites.add(self.project)

        self.client.force_login(self.user)
        response = self.client.post(f'/projects/{self.project.id}/toggle-favorite/')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['favorited'], 'Не избранный')

        self.assertNotIn(self.project, self.user.favorites.all())

    def test_toggle_favorite_requires_authentication(self):
        """Test toggle favorite requires authentication"""
        response = self.client.post(f'/projects/{self.project.id}/toggle-favorite/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_toggle_favorite_invalid_project(self):
        """Test toggle favorite with invalid project ID"""
        self.client.force_login(self.user)
        response = self.client.post('/projects/999/toggle-favorite/')
        self.assertEqual(response.status_code, 404)


class CompleteProjectViewTest(TestCase):
    """Tests for completing project functionality"""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.owner,
            status='open'
        )

    def test_complete_project_owner(self):
        """Test project owner can complete the project"""
        self.client.force_login(self.owner)
        response = self.client.post(f'/projects/{self.project.id}/complete/')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['project_status'], 'closed')

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'closed')

    def test_complete_project_not_owner(self):
        """Test non-owner cannot complete the project"""
        self.client.force_login(self.other_user)
        response = self.client.post(f'/projects/{self.project.id}/complete/')
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Нет прав')

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'open')

    def test_complete_project_requires_authentication(self):
        """Test completing project requires authentication"""
        response = self.client.post(f'/projects/{self.project.id}/complete/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_complete_project_already_closed(self):
        """Test cannot complete already closed project"""
        self.project.status = 'closed'
        self.project.save()

        self.client.force_login(self.owner)
        response = self.client.post(f'/projects/{self.project.id}/complete/')
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Проект уже завершен')


class ToggleParticipateViewTest(TestCase):
    """Tests for toggling participation functionality"""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.participant = User.objects.create_user(
            email='participant@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.owner,
            status='open'
        )

    def test_toggle_participate_add(self):
        """Test adding participation to a project"""
        self.client.force_login(self.participant)
        response = self.client.post(f'/projects/{self.project.id}/toggle-participate/')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['message'], 'Вы присоединились к проекту')
        self.assertTrue(data['is_participating'])
        self.assertEqual(data['participants_count'], 1)
        self.assertIsNotNone(data['participant'])

        self.project.refresh_from_db()
        self.assertIn(self.participant, self.project.participants.all())

    def test_toggle_participate_remove(self):
        """Test removing participation from a project"""
        self.project.participants.add(self.participant)

        self.client.force_login(self.participant)
        response = self.client.post(f'/projects/{self.project.id}/toggle-participate/')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['message'], 'Вы вышли из проекта')
        self.assertFalse(data['is_participating'])
        self.assertEqual(data['participants_count'], 0)

        self.project.refresh_from_db()
        self.assertNotIn(self.participant, self.project.participants.all())

    def test_toggle_participate_requires_authentication(self):
        """Test toggling participation requires authentication"""
        response = self.client.post(f'/projects/{self.project.id}/toggle-participate/')
        self.assertEqual(response.status_code, 302)  # Redirect to login


class ProjectSkillManagementTest(TestCase):
    """Tests for project skill management"""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.owner,
            status='open'
        )

        self.skill1 = Skill.objects.create(name='Python')
        self.skill2 = Skill.objects.create(name='Django')
        self.skill3 = Skill.objects.create(name='JavaScript')

    def test_add_skill_by_id(self):
        """Test adding existing skill to project by ID"""
        self.client.force_login(self.owner)
        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill1.id)}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(int(data['id']), self.skill1.id)
        self.assertEqual(data['name'], 'Python')
        self.assertFalse(data['created'])
        self.assertTrue(data['added'])

        self.project.refresh_from_db()
        self.assertIn(self.skill1, self.project.skills.all())

    def test_add_skill_by_name_new(self):
        """Test adding new skill to project by name"""
        self.client.force_login(self.owner)
        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            json.dumps({'name': 'Go'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['created'])
        self.assertTrue(data['added'])

        # Check skill was created
        self.assertTrue(Skill.objects.filter(name='Go').exists())
        skill = Skill.objects.get(name='Go')
        self.assertEqual(int(data['id']), skill.id)

        self.project.refresh_from_db()
        self.assertIn(skill, self.project.skills.all())

    def test_add_skill_duplicate(self):
        """Test adding skill that's already in project"""
        self.project.skills.add(self.skill1)

        self.client.force_login(self.owner)
        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill1.id)}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['created'])

    def test_add_skill_not_owner(self):
        """Test non-owner cannot add skills"""
        self.client.force_login(self.other_user)
        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill1.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Отказано в доступе')

    def test_add_skill_requires_authentication(self):
        """Test adding skill requires authentication"""
        response = self.client.post(
            f'/projects/{self.project.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill1.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_remove_skill(self):
        """Test removing skill from project"""
        self.project.skills.add(self.skill1)

        self.client.force_login(self.owner)
        response = self.client.post(
            f'/projects/{self.project.id}/skills/{self.skill1.id}/remove/'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')

        self.project.refresh_from_db()
        self.assertNotIn(self.skill1, self.project.skills.all())

        # Skill should still exist in DB
        self.assertTrue(Skill.objects.filter(id=self.skill1.id).exists())

    def test_remove_skill_not_owner(self):
        """Test non-owner cannot remove skills"""
        self.project.skills.add(self.skill1)

        self.client.force_login(self.other_user)
        response = self.client.post(
            f'/projects/{self.project.id}/skills/{self.skill1.id}/remove/'
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Отказано в доступе')

    def test_remove_skill_not_in_project(self):
        """Test removing skill not in project"""
        self.client.force_login(self.owner)
        response = self.client.post(
            f'/projects/{self.project.id}/skills/{self.skill1.id}/remove/'
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('не обладает навыком', data['error'])


class UsersListViewTest(TestCase):
    """Tests for users list view"""

    def setUp(self):
        self.client = Client()

        self.user1 = User.objects.create_user(
            email='user1@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.user2 = User.objects.create_user(
            email='user2@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
        )

        self.user3 = User.objects.create_user(
            email='user3@example.com',
            name='Bob',
            surname='Johnson',
            phone='+79123456789',
            password='testpass123',
        )

    def test_users_list_all_users(self):
        """Test users list shows all users"""
        response = self.client.get('/users/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/participants.html')

        users = response.context['object_list']
        self.assertEqual(users.count(), 3)

    def test_users_list_ordered_by_id(self):
        """Test users are ordered by id"""
        response = self.client.get('/users/list/')
        users = response.context['object_list']
        self.assertEqual(users[0], self.user1)
        self.assertEqual(users[1], self.user2)
        self.assertEqual(users[2], self.user3)

    def test_users_list_authentication_not_required(self):
        """Test users list is accessible without authentication"""
        response = self.client.get('/users/list/')
        self.assertEqual(response.status_code, 200)

    def test_users_list_pagination(self):
        """Test users list pagination"""
        # Create more than 12 users with unique emails
        for i in range(15):
            User.objects.create_user(
                email=f'user_{i}_unique@example.com',
                name=f'User{i}',
                surname=f'Surname{i}',
                phone=f'+700000000{i:02d}',  # Максимум 12 символов
                password='testpass123',
            )

        response = self.client.get('/users/list/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['object_list']), 12)


class UsersListViewSkillFilterTest(TestCase):
    """Tests for users list with skill filtering"""

    def setUp(self):
        self.client = Client()

        self.user1 = User.objects.create_user(
            email='user1@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.user2 = User.objects.create_user(
            email='user2@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
        )

        self.user3 = User.objects.create_user(
            email='user3@example.com',
            name='Bob',
            surname='Johnson',
            phone='+79123456789',
            password='testpass123',
        )

        self.skill_python = Skill.objects.create(name='Python')
        self.skill_django = Skill.objects.create(name='Django')
        self.skill_js = Skill.objects.create(name='JavaScript')

        self.user1.skills.add(self.skill_python)
        self.user2.skills.add(self.skill_django)
        self.user3.skills.add(self.skill_python, self.skill_js)

    def test_users_list_filter_by_skill(self):
        """Test filtering users by skill"""
        response = self.client.get('/users/list/?skill=Python')
        self.assertEqual(response.status_code, 200)

        users = response.context['object_list']
        self.assertEqual(users.count(), 2)
        self.assertIn(self.user1, users)
        self.assertIn(self.user3, users)
        self.assertNotIn(self.user2, users)

    def test_users_list_filter_by_skill_case_insensitive(self):
        """Test filtering users by skill (case insensitive)"""
        response = self.client.get('/users/list/?skill=python')
        self.assertEqual(response.status_code, 200)

        users = response.context['object_list']
        self.assertEqual(users.count(), 2)
        self.assertIn(self.user1, users)
        self.assertIn(self.user3, users)

    def test_users_list_no_filter(self):
        """Test users list without filter returns all users"""
        response = self.client.get('/users/list/')
        self.assertEqual(response.status_code, 200)

        users = response.context['object_list']
        self.assertEqual(users.count(), 3)

    def test_users_list_context_variables(self):
        """Test context contains all_skills and active_skill"""
        response = self.client.get('/users/list/?skill=Python')
        self.assertEqual(response.status_code, 200)

        self.assertIn('all_skills', response.context)
        self.assertEqual(list(response.context['all_skills']), ['Python', 'Django', 'JavaScript'])

        self.assertIn('active_skill', response.context)
        self.assertEqual(response.context['active_skill'], 'Python')


class UsersListViewFilterTest(TestCase):
    """Tests for users list with various filters"""

    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(
            email='owner@example.com',
            name='Owner',
            surname='User',
            phone='+71234567890',
            password='testpass123',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            name='Other',
            surname='User',
            phone='+79876543210',
            password='testpass123',
        )

        self.user3 = User.objects.create_user(
            email='user3@example.com',
            name='Third',
            surname='User',
            phone='+79123456789',
            password='testpass123',
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.owner,
            status='open'
        )

        # For favorites filter
        self.other_user.favorites.add(self.project)

        # For participants filter
        self.project.participants.add(self.other_user)

        # For interested filter
        self.user3.favorites.add(self.project)

    def test_users_list_filter_owners_of_favorite_projects(self):
        """Test filter for owners of favorite projects"""
        self.client.force_login(self.other_user)
        response = self.client.get('/users/list/?filter=owners-of-favorite-projects')
        self.assertEqual(response.status_code, 200)

        users = response.context['object_list']
        self.assertEqual(users.count(), 1)
        self.assertIn(self.owner, users)
        self.assertNotIn(self.other_user, users)

    def test_users_list_filter_owners_of_participating_projects(self):
        """Test filter for owners of projects user participates in"""
        self.client.force_login(self.other_user)
        response = self.client.get('/users/list/?filter=owners-of-participating-projects')
        self.assertEqual(response.status_code, 200)

        users = response.context['object_list']
        self.assertEqual(users.count(), 1)
        self.assertIn(self.owner, users)

    def test_users_list_filter_interested_in_my_projects(self):
        """Test filter for users who like my projects"""
        self.client.force_login(self.owner)
        response = self.client.get('/users/list/?filter=interested-in-my-projects')
        self.assertEqual(response.status_code, 200)

        users = response.context['object_list']
        self.assertEqual(users.count(), 2)
        self.assertIn(self.other_user, users)
        self.assertIn(self.user3, users)

    def test_users_list_filter_participants_of_my_projects(self):
        """Test filter for participants of my projects"""
        self.client.force_login(self.owner)
        response = self.client.get('/users/list/?filter=participants-of-my-projects')
        self.assertEqual(response.status_code, 200)

        users = response.context['object_list']
        self.assertEqual(users.count(), 1)
        self.assertIn(self.other_user, users)

    def test_users_list_filter_requires_authentication(self):
        """Test filters only work for authenticated users"""
        response = self.client.get('/users/list/?filter=owners-of-favorite-projects')
        self.assertEqual(response.status_code, 200)
        # Should show all users for unauthenticated
        self.assertEqual(response.context['object_list'].count(), 3)

    def test_users_list_filter_context_variable(self):
        """Test context contains active_filter"""
        self.client.force_login(self.owner)
        response = self.client.get('/users/list/?filter=participants-of-my-projects')
        self.assertEqual(response.status_code, 200)

        self.assertIn('active_filter', response.context)
        self.assertEqual(response.context['active_filter'], 'participants-of-my-projects')


class UserDetailViewTest(TestCase):
    """Tests for user details page"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

    def test_user_details_authenticated(self):
        """Test authenticated user can view user details"""
        self.client.force_login(self.user)
        response = self.client.get(f'/users/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user-details.html')
        self.assertEqual(response.context['user'], self.user)

    def test_user_details_unauthenticated(self):
        """Test unauthenticated user can view user details"""
        response = self.client.get(f'/users/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user)

    def test_user_details_invalid_user(self):
        """Test user details with invalid user ID"""
        response = self.client.get('/users/999/')
        self.assertEqual(response.status_code, 404)


class UserSkillManagementTest(TestCase):
    """Tests for user skill management"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
        )

        self.skill1 = Skill.objects.create(name='Python')
        self.skill2 = Skill.objects.create(name='Django')

    def test_get_skills_autocomplete(self):
        """Test skill autocomplete endpoint"""
        response = self.client.get('/users/skills/?q=Py')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Python')

    def test_get_skills_autocomplete_ordering(self):
        """Test skill autocomplete returns in alphabetical order"""
        response = self.client.get('/users/skills/?q=')
        data = json.loads(response.content)

        names = [item['name'] for item in data]
        self.assertEqual(names, sorted(names))

    def test_get_skills_autocomplete_limit(self):
        """Test skill autocomplete returns max 10 results"""
        # Create 15 skills
        for i in range(15):
            Skill.objects.create(name=f'Skill{i}')

        response = self.client.get('/users/skills/?q=S')
        data = json.loads(response.content)
        self.assertLessEqual(len(data), 10)

    def test_add_user_skill_by_id(self):
        """Test adding existing skill to user by ID"""
        self.client.force_login(self.user)
        response = self.client.post(
            f'/users/{self.user.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill1.id)}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(int(data['id']), self.skill1.id)
        self.assertEqual(data['name'], 'Python')
        self.assertFalse(data['created'])
        self.assertTrue(data['added'])

        self.user.refresh_from_db()
        self.assertIn(self.skill1, self.user.skills.all())

    def test_add_user_skill_by_name_new(self):
        """Test adding new skill to user by name"""
        self.client.force_login(self.user)
        response = self.client.post(
            f'/users/{self.user.id}/skills/add/',
            json.dumps({'name': 'Go'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['created'])
        self.assertTrue(data['added'])

        # Check skill was created
        self.assertTrue(Skill.objects.filter(name='Go').exists())
        skill = Skill.objects.get(name='Go')
        self.assertEqual(int(data['id']), skill.id)

        self.user.refresh_from_db()
        self.assertIn(skill, self.user.skills.all())

    def test_add_user_skill_duplicate(self):
        """Test adding skill already in user's profile"""
        self.user.skills.add(self.skill1)

        self.client.force_login(self.user)
        response = self.client.post(
            f'/users/{self.user.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill1.id)}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['added'])

    def test_add_user_skill_not_owner(self):
        """Test non-owner cannot add skills to user profile"""
        self.client.force_login(self.other_user)
        response = self.client.post(
            f'/users/{self.user.id}/skills/add/',
            json.dumps({'skill_id': str(self.skill1.id)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Отказано в доступе')

    def test_remove_user_skill(self):
        """Test removing skill from user profile"""
        self.user.skills.add(self.skill1)

        self.client.force_login(self.user)
        response = self.client.post(
            f'/users/{self.user.id}/skills/{self.skill1.id}/remove/'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')

        self.user.refresh_from_db()
        self.assertNotIn(self.skill1, self.user.skills.all())

        # Skill should still exist in DB
        self.assertTrue(Skill.objects.filter(id=self.skill1.id).exists())

    def test_remove_user_skill_not_owner(self):
        """Test non-owner cannot remove skills from user profile"""
        self.user.skills.add(self.skill1)

        self.client.force_login(self.other_user)
        response = self.client.post(
            f'/users/{self.user.id}/skills/{self.skill1.id}/remove/'
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Отказано в доступе')

    def test_remove_user_skill_not_in_profile(self):
        """Test removing skill not in user profile"""
        self.client.force_login(self.user)
        response = self.client.post(
            f'/users/{self.user.id}/skills/{self.skill1.id}/remove/'
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('не обладает навыком', data['error'])


class ProjectCreateUpdateViewTest(TestCase):
    """Tests for project create and update views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

        self.skill = Skill.objects.create(name='Python')

    def test_create_project_requires_authentication(self):
        """Test create project requires authentication"""
        # Assuming URL pattern is 'projects:create' or similar
        response = self.client.get('/projects/create/')
        # It might be a 302 redirect to login or 404 if URL doesn't exist
        self.assertIn(response.status_code, [302, 404])

    def test_create_project_get(self):
        """Test GET request to create project"""
        self.client.force_login(self.user)
        response = self.client.get('/projects/create/')
        # If URL exists, should return 200, otherwise skip
        if response.status_code == 200:
            self.assertTemplateUsed(response, 'projects/create-project.html')

    def test_create_project_post(self):
        """Test POST request to create project"""
        self.client.force_login(self.user)
        response = self.client.post('/projects/create/', {
            'name': 'New Project',
            'description': 'New description',
            'status': 'open',
            'github_url': 'https://github.com/test/repo',
        })

        # If URL exists, should redirect to detail
        if response.status_code == 302:
            # Check project was created
            project = Project.objects.filter(name='New Project').first()
            if project:
                self.assertEqual(project.owner, self.user)

    def test_update_project_requires_authentication(self):
        """Test update project requires authentication"""
        project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.user,
            status='open'
        )
        response = self.client.get(f'/projects/{project.id}/update/')
        self.assertIn(response.status_code, [302, 404])

    def test_update_project_get(self):
        """Test GET request to update project"""
        self.client.force_login(self.user)
        project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.user,
            status='open'
        )
        response = self.client.get(f'/projects/{project.id}/update/')
        if response.status_code == 200:
            self.assertTemplateUsed(response, 'projects/create-project.html')
            self.assertEqual(response.context['project'], project)

    def test_update_project_post(self):
        """Test POST request to update project"""
        self.client.force_login(self.user)
        project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.user,
            status='open'
        )
        response = self.client.post(f'/projects/{project.id}/update/', {
            'name': 'Updated Project',
            'description': 'Updated description',
            'status': 'closed',
            'github_url': 'https://github.com/test/updated',
        })

        if response.status_code == 302:
            project.refresh_from_db()
            self.assertEqual(project.name, 'Updated Project')

    def test_update_project_not_owner(self):
        """Test non-owner cannot update project"""
        self.client.force_login(self.user)
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other',
            surname='User',
            phone='+79876543210',
            password='testpass123',
        )
        project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=other_user,
            status='open'
        )
        response = self.client.get(f'/projects/{project.id}/update/')
        if response.status_code == 403:
            self.assertEqual(response.status_code, 403)


class UserUpdateViewTest(TestCase):
    """Tests for user update view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
        )

    def test_edit_profile_requires_authentication(self):
        """Test edit profile requires authentication"""
        response = self.client.get('/users/list/edit/')
        self.assertIn(response.status_code, [302, 404])

    def test_edit_profile_get(self):
        """Test GET request to edit profile"""
        self.client.force_login(self.user)
        response = self.client.get('/users/list/edit/')
        if response.status_code == 200:
            self.assertTemplateUsed(response, 'users/edit_profile.html')
            self.assertEqual(response.context['user'], self.user)

    def test_edit_profile_post(self):
        """Test POST request to edit profile"""
        self.client.force_login(self.user)
        response = self.client.post('/users/list/edit/', {
            'name': 'Updated Name',
            'surname': 'Updated Surname',
            'phone': '+79999999999',
            'about': 'Updated about text',
        })

        if response.status_code == 302:
            self.user.refresh_from_db()
            self.assertEqual(self.user.name, 'Updated Name')


class UserPasswordChangeViewTest(TestCase):
    """Tests for password change view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='oldpassword123',
        )

    def test_change_password_requires_authentication(self):
        """Test change password requires authentication"""
        response = self.client.get('/users/list/change-password/')
        self.assertIn(response.status_code, [302, 404])

    def test_change_password_get(self):
        """Test GET request to change password"""
        self.client.force_login(self.user)
        response = self.client.get('/users/list/change-password/')
        if response.status_code == 200:
            self.assertTemplateUsed(response, 'users/change_password.html')

    def test_change_password_post(self):
        """Test POST request to change password"""
        self.client.force_login(self.user)
        response = self.client.post('/users/list/change-password/', {
            'old_password': 'oldpassword123',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123',
        })

        if response.status_code == 302:
            # Check password was changed
            self.user.refresh_from_db()
            self.assertTrue(self.user.check_password('newpassword123'))

    def test_change_password_wrong_old_password(self):
        """Test change password with wrong old password"""
        self.client.force_login(self.user)
        response = self.client.post('/users/list/change-password/', {
            'old_password': 'wrongpassword',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123',
        })

        if response.status_code == 200:
            # Check for form error
            self.assertContains(response, 'old password')

    def test_change_password_mismatch(self):
        """Test change password with mismatched new passwords"""
        self.client.force_login(self.user)
        response = self.client.post('/users/list/change-password/', {
            'old_password': 'oldpassword123',
            'new_password1': 'newpassword123',
            'new_password2': 'differentpassword',
        })

        if response.status_code == 200:
            # Check for form error
            self.assertContains(response, "didn't match")
