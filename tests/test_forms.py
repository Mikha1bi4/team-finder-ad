# tests/test_forms.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.forms import PasswordChangeForm
from PIL import Image
import io
from users.forms import (
    UserRegisterForm, UserLoginForm, UserUpdateForm
)
from projects.forms import ProjectForm

User = get_user_model()


class UserRegisterFormTest(TestCase):
    """Tests for user registration form"""

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

    def test_valid_registration_form(self):
        """Test valid registration form"""
        form_data = {
            'email': 'test@example.com',
            'name': 'John',
            'surname': 'Doe',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }

        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        """Test invalid email format"""
        form_data = {
            'email': 'invalid-email',
            'name': 'John',
            'surname': 'Doe',
            'password': 'testpass123',
            'password2': 'testpass123'
        }

        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch(self):
        """Test password mismatch"""
        form_data = {
            'email': 'test@example.com',
            'name': 'John',
            'surname': 'Doe',
            'password1': 'testpass123',
            'password2': 'differentpass'
        }

        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_email_duplicate(self):
        """Test duplicate email"""
        # Create first user
        User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            password='testpass123',
            avatar=self.create_test_image()
        )

        # Try to create second user with same email
        form_data = {
            'email': 'test@example.com',
            'name': 'Jane',
            'surname': 'Smith',
            'password': 'testpass123',
            'password2': 'testpass123'
        }

        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class UserLoginFormTest(TestCase):
    """Tests for user login form"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png', b'content', content_type='image/png')
        )

    def test_valid_login_form(self):
        """Test valid login form"""
        form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }

        form = UserLoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_credentials(self):
        """Test invalid credentials"""
        form_data = {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        }

        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        # # Пример form.errors:
        # {
        #     'email': ['Введите корректный email'],  # Ошибка у поля email
        #     '__all__': ['Неверный email или пароль']  # Общая ошибка формы
        # }

    def test_nonexistent_email(self):
        """Test nonexistent email"""
        form_data = {
            'username': 'nonexistent@example.com',
            'password': 'testpass123'
        }

        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_inactive_user(self):
        """Test inactive user cannot login"""
        self.user.is_active = False
        self.user.save()

        form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }

        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class UserUpdateFormTest(TestCase):
    """Tests for user profile form"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png', b'content', content_type='image/png')
        )

    def create_test_image(self):
        """Create a test image for avatar"""
        image = Image.new('RGB', (100, 100), color='red')
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        return SimpleUploadedFile(
            'new_avatar.png',
            image_bytes.getvalue(),
            content_type='image/png'
        )

    def test_valid_update_form(self):
        """Test valid update form"""

        form_data = {
            'name': 'John',
            'surname': 'Doe',
            'about': 'Test about text',
            'phone': '+71234567890',
            'github_url': 'https://github.com/johndoe'
        }

        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_phone_starts_with_proper_number(self):
        """Test invalid phone number format"""

        form_data = {
            'name': 'John',
            'surname': 'Doe',
            'phone': '52345678961',
            'about': 'Test about text',
            'github_url': 'https://github.com/johndoe'

        }

        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_phone_is_too_long(self):
        """Test invalid phone number format"""

        form_data = {
            'name': 'John',
            'surname': 'Doe',
            'phone': '87686786752345678961',
            'about': 'Test about text',
            'github_url': 'https://github.com/johndoe'

        }

        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_phone_is_too_short(self):
        """Test invalid phone number format"""

        form_data = {
            'name': 'John',
            'surname': 'Doe',
            'phone': '8561',
            'about': 'Test about text',
            'github_url': 'https://github.com/johndoe'

        }

        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_phone_includes_letters(self):
        """Test invalid phone number format"""

        form_data = {
            'name': 'John',
            'surname': 'Doe',
            'phone': '8237tsg54qa',
            'about': 'Test about text',
            'github_url': 'https://github.com/johndoe'

        }

        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_phone_duplicate(self):
        """Тест: проверка дубликата телефона"""

        user2 = User.objects.create_user(
            email='test2@example.com',
            name='John2',
            surname='Doe2',
            phone='+71234567892',  # Уникальный телефон
            password='testpass123',
            avatar=self.create_test_image()
        )

        form_data = {
            'name': 'John2',
            'surname': 'Doe2',
            'phone': '+71234567890',  # Этот телефон уже у user1
            'about': 'Test about text',
            'github_url': 'https://github.com/johndoe2'
        }

        form = UserUpdateForm(data=form_data, instance=user2)

        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        user2.refresh_from_db()
        self.assertEqual(user2.phone, '+71234567892')

    def test_phone_unique_with_different_format(self):
        """Test phone uniqueness with different format"""

        user2 = User.objects.create_user(
            email='test2@example.com',
            name='John2',
            surname='Doe2',
            phone='+71234567892',  # Уникальный телефон
            password='testpass123',
            avatar=self.create_test_image()
        )

        form_data = {
            'name': 'John2',
            'surname': 'Doe2',
            'phone': '81234567890',  # Этот телефон уже у self.user
            'about': 'Test about text',
            'github_url': 'https://github.com/johndoe2'
        }

        form = UserUpdateForm(data=form_data, instance=user2)

        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        user2.refresh_from_db()
        self.assertEqual(user2.phone, '+71234567892')

    def test_phone_duplicate_when_updating_same_user(self):
        """Тест: обновление того же пользователя должно работать"""

        # Пытаемся обновить того же пользователя с тем же телефоном
        form_data = {
            'name': 'John',
            'surname': 'Doe',
            'phone': '+71234567890',  # Тот же телефон
            'about': 'New about text',
        }

        form = UserUpdateForm(data=form_data, instance=self.user)

        # Должно быть валидно (это тот же пользователь)
        self.assertTrue(form.is_valid())

    def test_phone_normalization(self):
        """Test phone number normalization"""

        form = UserUpdateForm(data={
            'name': 'John',
            'surname': 'Doe',
            'phone': '81234567890',
            'github_url': 'https://github.com/johndoe'
        }, instance=self.user)

        self.assertTrue(form.is_valid())
        # The form should normalize to +7 format
        self.assertEqual(form.cleaned_data['phone'], '+71234567890')

    def test_invalid_github_url(self):
        """Test invalid GitHub URL"""

        form_data = {
            'name': 'John',
            'surname': 'Doe',
            'phone': '+71234567890',
            'github_url': 'not-a-url'
        }

        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('github_url', form.errors)

    def test_non_github_url(self):
        """Test non-GitHub URL"""

        form_data = {
            'name': 'John',
            'surname': 'Doe',
            'phone': '+71234567890',
            'github_url': 'https://google.com'
        }

        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('github_url', form.errors)


class ProjectFormTest(TestCase):
    """Tests for project form"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='John',
            surname='Doe',
            phone='+71234567890',
            password='testpass123',
            avatar=SimpleUploadedFile('avatar.png', b'content', content_type='image/png')
        )

    def test_valid_project_form(self):
        """Test valid project form"""
        form_data = {
            'name': 'Test Project',
            'description': 'Test description',
            'github_url': 'https://github.com/test/project',
            'status': 'open'
        }

        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_name(self):
        """Test missing name field"""
        form_data = {
            'description': 'Test description',
            'github_url': 'https://github.com/test/project',
            'status': 'open'
        }

        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_name_max_length(self):
        """Test name exceeds max length"""
        form_data = {
            'name': 'A' * 201,  # 201 characters
            'description': 'Test description',
            'github_url': 'https://github.com/test/project',
            'status': 'open'
        }

        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_invalid_github_url(self):
        """Test invalid GitHub URL"""
        form_data = {
            'name': 'Test Project',
            'description': 'Test description',
            'github_url': 'not-a-url',
            'status': 'open'
        }

        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('github_url', form.errors)

    def test_non_github_url(self):
        """Test non-GitHub URL"""
        form_data = {
            'name': 'Test Project',
            'description': 'Test description',
            'github_url': 'https://google.com',
            'status': 'open'
        }

        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('github_url', form.errors)

    def test_valid_status_choices(self):
        """Test valid status choices"""
        form_data = {
            'name': 'Test Project',
            'description': 'Test description',
            'github_url': 'https://github.com/test/project',
            'status': 'open'
        }

        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())

        form_data['status'] = 'closed'
        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_status(self):
        """Test invalid status"""
        form_data = {
            'name': 'Test Project',
            'description': 'Test description',
            'github_url': 'https://github.com/test/project',
            'status': 'invalid'
        }

        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_empty_description_allowed(self):
        """Test empty description is allowed"""
        form_data = {
            'name': 'Test Project',
            'description': '',
            'github_url': 'https://github.com/test/project',
            'status': 'open'
        }

        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_empty_github_url_allowed(self):
        """Test empty GitHub URL is allowed"""
        form_data = {
            'name': 'Test Project',
            'description': 'Test description',
            'github_url': '',
            'status': 'open'
        }

        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())
