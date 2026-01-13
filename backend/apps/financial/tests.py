from decimal import Decimal
from apps.financial.models import Deposit, FinancialAccount

class DepositTests(APITestCase):
    """Test deposit creation and approval"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+254712345678',
            full_name='Test User',
            password='TestPass123!',
            email_verified=True,
            is_active=True
        )
        self.admin = User.objects.create_user(
            email='admin@example.com',
            phone_number='+254712345679',
            full_name='Admin User',
            password='AdminPass123!',
            role='admin',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.deposit_url = reverse('deposit-list')
    
    def test_create_deposit(self):
        """Test creating a deposit"""
        data = {
            'amount': 20000,
            'payment_method': 'mpesa',
            'mpesa_phone': '+254712345678'
        }
        
        response = self.client.post(self.deposit_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Deposit.objects.count(), 1)
        
        deposit = Deposit.objects.first()
        self.assertEqual(deposit.user, self.user)
        self.assertEqual(deposit.status, 'pending')
        self.assertEqual(deposit.amount, Decimal('20000.00'))
    
    def test_cannot_create_multiple_deposits_same_month(self):
        """Test that user cannot create multiple deposits in same month"""
        # Create first deposit
        Deposit.objects.create(
            user=self.user,
            amount=20000,
            payment_method='mpesa',
            status='completed',
            transaction_reference='TEST001'
        )
        
        # Try to create second deposit
        data = {
            'amount': 20000,
            'payment_method': 'mpesa',
            'mpesa_phone': '+254712345678'
        }
        
        response = self.client.post(self.deposit_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_admin_approve_deposit(self):
        """Test admin approving a deposit"""
        deposit = Deposit.objects.create(
            user=self.user,
            amount=20000,
            payment_method='mpesa',
            status='pending',
            transaction_reference='TEST001'
        )
        
        # Login as admin
        self.client.force_authenticate(user=self.admin)
        
        approve_url = reverse('deposit-approve-deposit', kwargs={'pk': deposit.id})
        response = self.client.post(approve_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        deposit.refresh_from_db()
        self.assertEqual(deposit.status, 'completed')
        self.assertEqual(deposit.approved_by, self.admin)
        
        # Check financial account updated
        account = FinancialAccount.objects.get(user=self.user)
        self.assertEqual(account.total_contributions, Decimal('20000.00'))
        self.assertGreater(account.interest_earned, 0)