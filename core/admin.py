from django.contrib import admin
from .models import Borrower, Loan, Saving, Branch, LoanOfficer, Organization

# ---------------- Borrower ----------------
@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'unique_id',
        'business',
        'mobile',
        'email',
        'total_paid',
        'loan_balance',
        'status',
        'organization',
        'branch'
    )
    search_fields = ('full_name', 'unique_id', 'mobile', 'business')
    list_filter = ('organization', 'branch', 'status')






# ---------------- Loan ----------------
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'borrower_name',   # Custom property
        'id',              # Django model ID as loan identifier
        'principal',
        'interest_rate',
        'total_due',
        'paid',
        'balance',
        'last_repayment',  # Custom property
        'status',
        'organization',
        'branch'
    )
    search_fields = ('borrower__full_name', 'id')
    list_filter = ('status', 'organization', 'branch')

    # Custom properties for admin display
    def borrower_name(self, obj):
        return obj.borrower.full_name if obj.borrower else '-'
    borrower_name.short_description = 'Borrower'

    def last_repayment(self, obj):
        last = obj.repayment_set.order_by('-date').first()
        return last.date if last else '-'
    last_repayment.short_description = 'Last Payment'
    
    
    
# ---------------- Saving ----------------
@admin.register(Saving)
class SavingAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'account_number',
        'product',
        'ledger_balance',
        'last_transaction',
        'status',
        'organization',
        'borrower'
    )
    search_fields = ('name', 'account_number', 'product', 'borrower__full_name')
    list_filter = ('status', 'organization', 'product')


# ---------------- Branch ----------------
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')
    search_fields = ('name',)
    list_filter = ('organization',)


# ---------------- Loan Officer ----------------
@admin.register(LoanOfficer)
class LoanOfficerAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'branch')
    search_fields = ('user__username',)
    list_filter = ('organization', 'branch')


# ---------------- Organization ----------------
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)