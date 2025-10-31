"""
Comprehensive tests for Category API endpoints.
"""

import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from categories.models import Category

User = get_user_model()


class CategoryAPITestCase(APITestCase):
    """Test cases for Category API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_category(self):
        """Test creating a new category."""
        url = reverse('category-list')
        data = {
            'name': 'Test Category',
            'description': 'A test category',
            'color': '#FF5733'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        
        category = Category.objects.first()
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.user, self.user)

    def test_list_categories(self):
        """Test listing categories."""
        # Create test categories
        Category.objects.create(
            user=self.user,
            name='Category 1',
            description='First category'
        )
        Category.objects.create(
            user=self.user,
            name='Category 2',
            description='Second category'
        )
        
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_retrieve_category(self):
        """Test retrieving a specific category."""
        category = Category.objects.create(
            user=self.user,
            name='Test Category',
            description='A test category'
        )
        
        url = reverse('category-detail', kwargs={'id': category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Category')

    def test_update_category(self):
        """Test updating a category."""
        category = Category.objects.create(
            user=self.user,
            name='Original Name',
            description='Original description'
        )
        
        url = reverse('category-detail', kwargs={'id': category.id})
        data = {
            'name': 'Updated Name',
            'description': 'Updated description'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category.refresh_from_db()
        self.assertEqual(category.name, 'Updated Name')

    def test_delete_category(self):
        """Test deleting a category."""
        category = Category.objects.create(
            user=self.user,
            name='Test Category'
        )
        
        url = reverse('category-detail', kwargs={'id': category.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_category_stats(self):
        """Test getting category statistics."""
        category = Category.objects.create(
            user=self.user,
            name='Test Category'
        )
        
        url = reverse('category-stats', kwargs={'id': category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('forms_count', response.data)
        self.assertIn('processes_count', response.data)

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access categories."""
        self.client.logout()
        
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_access_other_user_categories(self):
        """Test that users cannot access other users' categories."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            username='otheruser'
        )
        
        other_category = Category.objects.create(
            user=other_user,
            name='Other User Category'
        )
        
        url = reverse('category-detail', kwargs={'id': other_category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategoryCRUDTestCase(APITestCase):
    """Test cases for Category CRUD operations."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_category_success(self):
        """Test successful category creation."""
        url = reverse('category-list')
        data = {
            'name': 'Test Category',
            'description': 'A test category',
            'color': '#FF5733'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        
        category = Category.objects.first()
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.description, 'A test category')
        self.assertEqual(category.color, '#FF5733')
        self.assertEqual(category.user, self.user)

    def test_create_category_minimal_data(self):
        """Test category creation with minimal required data."""
        url = reverse('category-list')
        data = {'name': 'Minimal Category'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        category = Category.objects.first()
        self.assertEqual(category.name, 'Minimal Category')
        self.assertIsNone(category.description)
        self.assertIsNone(category.color)

    def test_create_category_validation_errors(self):
        """Test category creation with validation errors."""
        url = reverse('category-list')
        
        # Test empty name
        data = {'name': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test name too short
        data = {'name': 'A'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test name too long
        data = {'name': 'A' * 256}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid color
        data = {'name': 'Test', 'color': 'invalid'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_category_duplicate_name(self):
        """Test creating category with duplicate name."""
        # Create first category
        Category.objects.create(user=self.user, name='Duplicate Test')
        
        url = reverse('category-list')
        data = {'name': 'Duplicate Test'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', str(response.data))

    def test_list_categories_empty(self):
        """Test listing categories when none exist."""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['pagination']['total'], 0)

    def test_list_categories_with_pagination(self):
        """Test listing categories with pagination."""
        # Create 25 categories
        for i in range(25):
            Category.objects.create(
                user=self.user,
                name=f'Category {i}',
                description=f'Description {i}'
            )
        
        url = reverse('category-list')
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['pagination']['total'], 25)
        self.assertEqual(response.data['pagination']['pages'], 3)
        self.assertTrue(response.data['pagination']['has_next'])

    def test_list_categories_search(self):
        """Test searching categories."""
        Category.objects.create(user=self.user, name='HR Forms', description='Human resources')
        Category.objects.create(user=self.user, name='Marketing', description='Marketing campaigns')
        Category.objects.create(user=self.user, name='Finance', description='Financial forms')
        
        url = reverse('category-list')
        
        # Search by name
        response = self.client.get(url, {'search': 'HR'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'HR Forms')
        
        # Search by description
        response = self.client.get(url, {'search': 'campaigns'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Marketing')

    def test_retrieve_category_success(self):
        """Test successful category retrieval."""
        category = Category.objects.create(
            user=self.user,
            name='Test Category',
            description='A test category',
            color='#FF5733'
        )
        
        url = reverse('category-detail', kwargs={'id': category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Category')
        self.assertEqual(response.data['description'], 'A test category')
        self.assertEqual(response.data['color'], '#FF5733')

    def test_retrieve_category_not_found(self):
        """Test retrieving non-existent category."""
        fake_id = uuid.uuid4()
        url = reverse('category-detail', kwargs={'id': fake_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_category_full_update(self):
        """Test full category update (PUT)."""
        category = Category.objects.create(
            user=self.user,
            name='Original Name',
            description='Original description',
            color='#FF5733'
        )
        
        url = reverse('category-detail', kwargs={'id': category.id})
        data = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'color': '#3498DB'
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category.refresh_from_db()
        self.assertEqual(category.name, 'Updated Name')
        self.assertEqual(category.description, 'Updated description')
        self.assertEqual(category.color, '#3498DB')

    def test_update_category_partial_update(self):
        """Test partial category update (PATCH)."""
        category = Category.objects.create(
            user=self.user,
            name='Original Name',
            description='Original description',
            color='#FF5733'
        )
        
        url = reverse('category-detail', kwargs={'id': category.id})
        data = {'name': 'Updated Name Only'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category.refresh_from_db()
        self.assertEqual(category.name, 'Updated Name Only')
        self.assertEqual(category.description, 'Original description')  # Unchanged
        self.assertEqual(category.color, '#FF5733')  # Unchanged

    def test_update_category_validation_errors(self):
        """Test category update with validation errors."""
        category = Category.objects.create(user=self.user, name='Test Category')
        
        url = reverse('category-detail', kwargs={'id': category.id})
        
        # Test empty name
        data = {'name': ''}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid color
        data = {'color': 'invalid'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_category_success(self):
        """Test successful category deletion."""
        category = Category.objects.create(user=self.user, name='Test Category')
        
        url = reverse('category-detail', kwargs={'id': category.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_delete_category_not_found(self):
        """Test deleting non-existent category."""
        fake_id = uuid.uuid4()
        url = reverse('category-detail', kwargs={'id': fake_id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategoryAdvancedFeaturesTestCase(APITestCase):
    """Test cases for advanced category features."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

    def test_category_stats_success(self):
        """Test getting category statistics."""
        category = Category.objects.create(
            user=self.user,
            name='Test Category',
            description='A test category'
        )
        
        url = reverse('category-stats', kwargs={'id': category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category_id'], str(category.id))
        self.assertEqual(response.data['name'], 'Test Category')
        self.assertEqual(response.data['forms_count'], 0)
        self.assertEqual(response.data['processes_count'], 0)
        self.assertEqual(response.data['total_items'], 0)

    def test_category_stats_not_found(self):
        """Test getting statistics for non-existent category."""
        fake_id = uuid.uuid4()
        url = reverse('category-stats', kwargs={'id': fake_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_delete_success(self):
        """Test successful bulk delete operation."""
        # Create multiple categories
        categories = []
        for i in range(5):
            category = Category.objects.create(
                user=self.user,
                name=f'Category {i}'
            )
            categories.append(category)
        
        url = reverse('category-bulk-delete')
        data = {'category_ids': [str(cat.id) for cat in categories]}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted_count'], 5)
        self.assertEqual(response.data['requested_count'], 5)
        self.assertTrue(response.data['success'])
        self.assertEqual(Category.objects.count(), 0)

    def test_bulk_delete_partial_success(self):
        """Test bulk delete with some non-existent categories."""
        category = Category.objects.create(user=self.user, name='Test Category')
        fake_id = uuid.uuid4()
        
        url = reverse('category-bulk-delete')
        data = {'category_ids': [str(category.id), str(fake_id)]}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted_count'], 1)
        self.assertEqual(response.data['requested_count'], 2)

    def test_bulk_delete_validation_errors(self):
        """Test bulk delete with validation errors."""
        url = reverse('category-bulk-delete')
        
        # Test empty list
        data = {'category_ids': []}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test too many categories
        data = {'category_ids': [str(uuid.uuid4()) for _ in range(51)]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid UUIDs
        data = {'category_ids': ['invalid-uuid']}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_most_used_categories(self):
        """Test getting most used categories."""
        # Create categories with different usage patterns
        # Note: This test assumes forms and processes will be linked to categories
        # For now, we'll test the basic functionality
        
        categories = []
        for i in range(10):
            category = Category.objects.create(
                user=self.user,
                name=f'Category {i}'
            )
            categories.append(category)
        
        url = reverse('category-most-used')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 5)  # Default limit

    def test_most_used_categories_with_limit(self):
        """Test getting most used categories with custom limit."""
        # Create categories
        for i in range(15):
            Category.objects.create(user=self.user, name=f'Category {i}')
        
        url = reverse('category-most-used')
        response = self.client.get(url, {'limit': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

    def test_most_used_categories_limit_validation(self):
        """Test most used categories with invalid limit."""
        # Create some categories first
        for i in range(25):
            Category.objects.create(user=self.user, name=f'Category {i}')
        
        url = reverse('category-most-used')
        
        # Test limit too high
        response = self.client.get(url, {'limit': 25})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 20)  # Should be capped at 20

    def test_list_categories_with_stats(self):
        """Test listing categories with statistics included."""
        Category.objects.create(user=self.user, name='Test Category')
        
        url = reverse('category-list')
        response = self.client.get(url, {'include_stats': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        # Note: forms_count and processes_count will be 0 until forms/processes are implemented
        self.assertIn('forms_count', response.data['results'][0])
        self.assertIn('processes_count', response.data['results'][0])

    def test_forms_endpoint_not_implemented(self):
        """Test that forms endpoint returns not implemented."""
        category = Category.objects.create(user=self.user, name='Test Category')
        
        url = reverse('category-forms', kwargs={'id': category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_processes_endpoint_not_implemented(self):
        """Test that processes endpoint returns not implemented."""
        category = Category.objects.create(user=self.user, name='Test Category')
        
        url = reverse('category-processes', kwargs={'id': category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_501_NOT_IMPLEMENTED)


class CategorySecurityTestCase(APITestCase):
    """Test cases for category security and permissions."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            username='user1',
            first_name='User',
            last_name='One'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            username='user2',
            first_name='User',
            last_name='Two'
        )

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access categories."""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_access_other_user_categories(self):
        """Test that users cannot access other users' categories."""
        # Create category for user1
        category = Category.objects.create(
            user=self.user1,
            name='User 1 Category'
        )
        
        # Authenticate as user2
        self.client.force_authenticate(user=self.user2)
        
        # Try to access user1's category
        url = reverse('category-detail', kwargs={'id': category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_user_categories(self):
        """Test that users cannot update other users' categories."""
        # Create category for user1
        category = Category.objects.create(
            user=self.user1,
            name='User 1 Category'
        )
        
        # Authenticate as user2
        self.client.force_authenticate(user=self.user2)
        
        # Try to update user1's category
        url = reverse('category-detail', kwargs={'id': category.id})
        data = {'name': 'Hacked Name'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_other_user_categories(self):
        """Test that users cannot delete other users' categories."""
        # Create category for user1
        category = Category.objects.create(
            user=self.user1,
            name='User 1 Category'
        )
        
        # Authenticate as user2
        self.client.force_authenticate(user=self.user2)
        
        # Try to delete user1's category
        url = reverse('category-detail', kwargs={'id': category.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_bulk_delete_other_user_categories(self):
        """Test that users cannot bulk delete other users' categories."""
        # Create categories for user1
        category1 = Category.objects.create(user=self.user1, name='User 1 Category 1')
        category2 = Category.objects.create(user=self.user1, name='User 1 Category 2')
        
        # Authenticate as user2
        self.client.force_authenticate(user=self.user2)
        
        # Try to bulk delete user1's categories
        url = reverse('category-bulk-delete')
        data = {'category_ids': [str(category1.id), str(category2.id)]}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted_count'], 0)  # No categories deleted
        self.assertEqual(Category.objects.count(), 2)  # Categories still exist


class CategoryValidationTestCase(APITestCase):
    """Test cases for category validation and edge cases."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

    def test_color_validation(self):
        """Test various color format validations."""
        url = reverse('category-list')
        
        # Test valid 6-digit hex
        data = {'name': 'Test', 'color': '#FF5733'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test valid 3-digit hex
        data = {'name': 'Test2', 'color': '#F53'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test hex without #
        data = {'name': 'Test3', 'color': 'FF5733'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test lowercase hex
        data = {'name': 'Test4', 'color': '#ff5733'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_color_validation_errors(self):
        """Test invalid color formats."""
        url = reverse('category-list')
        
        # Test invalid hex characters
        data = {'name': 'Test', 'color': '#GGGGGG'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test wrong length
        data = {'name': 'Test2', 'color': '#FF57'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test empty color
        data = {'name': 'Test3', 'color': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # Empty is allowed

    def test_description_length_validation(self):
        """Test description length validation."""
        url = reverse('category-list')
        
        # Test description too long
        long_description = 'A' * 1001
        data = {'name': 'Test', 'description': long_description}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test description at max length
        max_description = 'A' * 1000
        data = {'name': 'Test2', 'description': max_description}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_name_case_insensitive_uniqueness(self):
        """Test that category names are unique case-insensitively."""
        url = reverse('category-list')
        
        # Create first category
        data = {'name': 'Test Category'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to create category with same name but different case
        data = {'name': 'test category'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try with uppercase
        data = {'name': 'TEST CATEGORY'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pagination_edge_cases(self):
        """Test pagination with edge cases."""
        # Create exactly 20 categories
        for i in range(20):
            Category.objects.create(user=self.user, name=f'Category {i}')
        
        url = reverse('category-list')
        
        # Test page 1
        response = self.client.get(url, {'page': 1, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertTrue(response.data['pagination']['has_next'])
        
        # Test page 2
        response = self.client.get(url, {'page': 2, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertFalse(response.data['pagination']['has_next'])
        
        # Test page beyond available pages
        response = self.client.get(url, {'page': 5, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Django pagination returns the last page when page number is too high
        self.assertEqual(len(response.data['results']), 10)  # Last page with remaining items

    def test_page_size_validation(self):
        """Test page size validation."""
        url = reverse('category-list')
        
        # Test page size too large - should return validation error
        response = self.client.get(url, {'page_size': 101})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('page_size', response.data)
        
        # Test page size too small - should return validation error
        response = self.client.get(url, {'page_size': 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('page_size', response.data)
        
        # Test valid page size
        response = self.client.get(url, {'page_size': 50})
        self.assertEqual(response.status_code, status.HTTP_200_OK)