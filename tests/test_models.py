# tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from PIL import Image
import io
from datetime import datetime

from projects.models import Project, Skill
from users.models import User

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for User model across all variants"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'name': 'John',
            'surname': 'Doe',
            'phone': '+71234567890',
            'avatar': self.create_test_image(),
            'about': 'Test about text',
            'password': '1234',
        }

    def create_test_image(self):
        """Create a test image for avatar"""
        image = Image.new('RGB', (100, 100), color='red')
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        return SimpleUploadedFile(
            'avatar.png',
            image_bytes.getvalue(),
            content_type='image/png'
        )

    def test_create_user(self):
        """Test creating a user"""
        user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=self.create_test_image()
        )

        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'John')
        self.assertEqual(user.surname, 'Doe')
        self.assertEqual(user.phone, '+71234567890')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('testpass123'))

    def test_email_unique(self):
        """Test that email must be unique"""
        User.objects.create_user(**self.user_data)

        with self.assertRaises(ValidationError):
            User.objects.create_user(**self.user_data)

    def test_avatar_auto_generation(self):
        """Test avatar is auto-generated from first letter of name"""
        user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=None  # Should be auto-generated
        )

        # Refresh from DB
        user.refresh_from_db()
        self.assertIsNotNone(user.avatar)
        self.assertTrue(user.avatar.name.startswith('avatars/'))

    def test_str_method(self):
        """Test string representation"""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.email}"
        self.assertEqual(str(user), expected)


class ProjectModelTest(TestCase):
    """Tests for Project model across all variants"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png',
                                      b'content', content_type='image/png')
        )

        self.project_data = {
            'name': 'Test Project',
            'description': 'Test description',
            'owner': self.user,
            'github_url': 'https://github.com/test/project',
            'status': 'open'
        }

    def test_create_project(self):
        """Test creating a project"""
        project = Project.objects.create(**self.project_data)

        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.description, 'Test description')
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.github_url, 'https://github.com/test/project')
        self.assertEqual(project.status, 'open')
        self.assertIsNotNone(project.created_at)
        self.assertEqual(project.participants.count(), 0)

    def test_auto_created_at(self):
        """Test created_at is auto-populated"""
        project = Project.objects.create(**self.project_data)
        self.assertIsNotNone(project.created_at)
        self.assertIsInstance(project.created_at, datetime)

    def test_status_choices(self):
        """Test status field has correct choices"""
        project = Project.objects.create(**self.project_data)

        # Test valid statuses
        project.status = 'open'
        project.full_clean()
        project.save()

        project.status = 'closed'
        project.full_clean()
        project.save()

        # Test invalid status
        with self.assertRaises(ValidationError):
            project.status = 'invalid'
            project.full_clean()

    def test_owner_relationship(self):
        """Test user can access owned_projects"""
        project1 = Project.objects.create(**self.project_data)
        project2 = Project.objects.create(
            name='Another Project',
            description='Another description',
            owner=self.user,
            status='open'
        )

        owned_projects = self.user.owned_projects.all()
        self.assertEqual(owned_projects.count(), 2)
        self.assertIn(project1, owned_projects)
        self.assertIn(project2, owned_projects)

    def test_participants_relationship(self):
        """Test participants many-to-many relationship"""
        project = Project.objects.create(**self.project_data)

        participant = User.objects.create_user(
            email='participant@example.com',
            name='Jane',
            surname='Smith',
            phone='+79876543210',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar2.png',
                                      b'content', content_type='image/png')
        )

        project.participants.add(participant)

        self.assertEqual(project.participants.count(), 1)
        self.assertIn(participant, project.participants.all())

        # Test reverse relationship
        participated = participant.participating_projects.all()
        self.assertEqual(participated.count(), 1)
        self.assertIn(project, participated)

    def test_str_method(self):
        """Test string representation"""
        project = Project.objects.create(**self.project_data)
        self.assertEqual(str(project), project.name)

    def test_github_url_validation(self):
        """Test GitHub URL validation"""
        project = Project.objects.create(**self.project_data)

        # Valid GitHub URL
        project.github_url = 'https://github.com/test/repo'
        try:
            project.full_clean()
        except ValidationError:
            self.fail("Valid GitHub URL raised ValidationError")

        # Invalid URL
        project.github_url = 'not-a-url'
        with self.assertRaises(ValidationError):
            project.full_clean()

        # Non-GitHub URL
        project.github_url = 'https://google.com'
        with self.assertRaises(ValidationError):
            project.full_clean()

        # Empty is allowed
        project.github_url = ''
        try:
            project.full_clean()
        except ValidationError:
            self.fail("Empty GitHub URL raised ValidationError")


class SkillModelTest(TestCase):
    """Tests for Skill model (variants 2 and 3)"""

    def setUp(self):
        self.skill_data = {
            'name': 'Python'
        }

    def test_create_skill(self):
        """Test creating a skill"""
        skill = Skill.objects.create(**self.skill_data)

        self.assertEqual(skill.name, 'Python')
        self.assertEqual(str(skill), 'Python')

    def test_name_unique(self):
        """Test skill name is unique"""
        Skill.objects.create(**self.skill_data)

        with self.assertRaises(IntegrityError):
            Skill.objects.create(**self.skill_data)

    def test_skill_users_relationship_variant2(self):
        """Test Skill.users relationship (Variant 2)"""
        skill = Skill.objects.create(name='Python')

        user = User.objects.create_user(
            email='user@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png',
                                      b'content', content_type='image/png')
        )

        # Assuming user has a ManyToMany to Skill
        user.skills.add(skill)

        self.assertEqual(skill.users.count(), 1)
        self.assertIn(user, skill.users.all())

    def test_skill_projects_relationship_variant3(self):
        """Test Skill.projects relationship (Variant 3)"""
        skill = Skill.objects.create(name='Python')

        owner = User.objects.create_user(
            email='owner@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png',
                                      b'content', content_type='image/png')
        )

        project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=owner,
            status='open'
        )

        # Assuming project has a ManyToMany to Skill
        project.skills.add(skill)

        self.assertEqual(skill.projects.count(), 1)
        self.assertIn(project, skill.projects.all())


class Variant1SpecificTests(TestCase):
    """Tests specific to Variant 1"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png',
                                      b'content', content_type='image/png')
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.user,
            status='open'
        )

    def test_user_favorites_relationship(self):
        """Test favorites many-to-many relationship"""
        self.user.favorites.add(self.project)

        self.assertEqual(self.user.favorites.count(), 1)
        self.assertIn(self.project, self.user.favorites.all())

        # Test project.interested_users reverse relationship
        self.assertEqual(self.project.interested_users.count(), 1)
        self.assertIn(self.user, self.project.interested_users.all())


class Variant2SpecificTests(TestCase):
    """Tests specific to Variant 2"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png', b'content',
                                      content_type='image/png')
        )

        self.skill = Skill.objects.create(name='Python')

    def test_user_skills_relationship(self):
        """Test user skills ForeignKey relationship"""
        # Assuming user has a ForeignKey to Skill
        self.user.skills.add(self.skill)
        self.user.save()

        self.assertIn(self.skill, self.user.skills.all())
        self.assertEqual(self.skill.users.count(), 1)
        self.assertIn(self.user, self.skill.users.all())


class Variant3SpecificTests(TestCase):
    """Tests specific to Variant 3"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png', b'content',
                                      content_type='image/png')
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='Test description',
            owner=self.user,
            status='open'
        )

        self.skill = Skill.objects.create(name='Python')

    def test_project_skills_relationship(self):
        """Test project skills ForeignKey relationship"""
        # Assuming project has a ForeignKey to Skill
        self.project.skills.add(self.skill)
        self.project.save()

        self.assertEqual(self.skill.projects.count(), 1)
        self.assertIn(self.skill, self.project.skills.all())
        self.assertIn(self.project, self.skill.projects.all())
