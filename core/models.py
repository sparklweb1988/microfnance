from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum




class Organization(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Branch(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class LoanOfficer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username



class Borrower(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Delinquent', 'Delinquent'),
    ]

    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE)
    
    # Personal / business details
    full_name = models.CharField(max_length=200)
    business = models.CharField(max_length=200, blank=True, null=True)
    unique_id = models.CharField(max_length=50, unique=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Status
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return self.full_name

    # Computed fields
    @property
    def total_paid(self):
        """Sum of all repayments made by this borrower"""
        loans = self.loan_set.all()
        total = sum([loan.paid for loan in loans], Decimal('0.00'))
        return total.quantize(Decimal('0.01'))

    @property
    def loan_balance(self):
        """Outstanding balance across all loans"""
        loans = self.loan_set.all()
        balance = sum([loan.balance for loan in loans], Decimal('0.00'))
        return balance.quantize(Decimal('0.01'))




class Loan(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Overdue', 'Overdue'),
        ('PAR30', 'PAR30'),
        ('Closed', 'Closed'),
    ]

    # Relationships
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, null=True)
    borrower = models.ForeignKey('Borrower', on_delete=models.CASCADE, null=True)
    officer = models.ForeignKey('LoanOfficer', on_delete=models.CASCADE, null=True)

    # Core financial fields
    principal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fees = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    penalty = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tenure = models.PositiveIntegerField(
        default=30,  # in days
        validators=[MinValueValidator(1)]
    )

    # Status & dates
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    disbursed_date = models.DateField(default=now)
    maturity = models.DateField(blank=True, null=True)

    # Payment tracking
    paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    last_payment_date = models.DateField(blank=True, null=True)

    # Auto-calculated properties
    @property
    def interest(self):
        """Simple interest based on principal"""
        return (self.principal * self.interest_rate / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def total_due(self):
        """Total amount due including fees and penalty"""
        return (self.principal + self.interest + self.fees + self.penalty).quantize(Decimal('0.01'))

    @property
    def balance(self):
        """Outstanding balance"""
        return (self.total_due - self.paid).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        """Auto-calculate maturity date and ensure proper totals"""
        if self.disbursed_date and self.tenure:
            self.maturity = self.disbursed_date + timedelta(days=self.tenure)

        # Optional: automatically mark loan as closed if fully paid
        if self.paid >= self.total_due:
            self.status = 'Closed'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.borrower.name} - {self.principal} ({self.status})"
    
    
    

class Repayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="repayments")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    date = models.DateField(auto_now_add=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Repayment of {self.amount} for loan {self.loan.id}"


class CollectionSheet(models.Model):
    loan_officer = models.ForeignKey(LoanOfficer, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Collection Sheet by {self.loan_officer.user.username} on {self.date}"


class CollectionItem(models.Model):
    sheet = models.ForeignKey(CollectionSheet, on_delete=models.CASCADE, related_name="items")
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])

    def __str__(self):
        return f"Collection of {self.amount} for Loan {self.loan.id}"





from django.db.models import Sum

class PostingBatch(models.Model):
    officer = models.ForeignKey(LoanOfficer, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    @property
    def total_amount(self):
        # Sum all related PostingItem amounts
        total = self.items.aggregate(sum=Sum('amount'))['sum'] or 0
        return total

    def __str__(self):
        return f"Batch {self.id} by {self.officer.user.username}"

class PostingItem(models.Model):
    batch = models.ForeignKey(PostingBatch, on_delete=models.CASCADE, related_name="items")
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.amount} for loan {self.loan.id}"
    
    
    
    
class Saving(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Dormant', 'Dormant'),
    ]

    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    borrower = models.ForeignKey('Borrower', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50, unique=True)
    product = models.CharField(max_length=100)
    ledger_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_transaction = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return f"{self.name} - {self.account_number}"
    
    
    
    
    
class Vendor(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name







class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Rent', 'Rent'),
        ('Salary', 'Salary'),
        ('Fuel', 'Fuel'),
        ('Utilities', 'Utilities'),
        ('Maintenance', 'Maintenance'),
        ('Other', 'Other'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=now)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.category} - ₦{self.amount}"
