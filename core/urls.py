from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Borrowers
    path('borrowers/', views.borrowers_view, name='borrowers'),
    path('borrowers/add/', views.add_borrower, name='add_borrower'),

    # Loans
    path('loans/', views.loans_view, name='loans'),
    path('loans/add/', views.add_loan, name='add_loan'),
    path('loans/par30/', views.par30_loans, name='par30_loans'),
    path('loans/overdue/', views.overdue_loans, name='overdue_loans'),

    # Savings
    path('savings/', views.savings_view, name='savings'),
    path('savings/add/', views.add_saving, name='add_saving'),

    # Collection Sheets / Repayments
    path('collection-sheet/', views.collection_sheet, name='collection_sheet'),
    # path('collection-sheet/add/', views.add_collection, name='add_collection'),
    path('repayments/', views.repayments_view, name='repayments'),
    path('repayments/add/', views.add_repayment, name='add_repayment'),

 
    # Reports
    path('reports/daily/', views.daily_collections_report, name='daily_collections_report'),
    # path('reports/monthly/', views.monthly_collections_report, name='monthly_collections_report'),
    path('reports/performance/', views.officer_performance, name='officer_performance'),
    # Bulk Batch Report (custom date range)
    # path('reports/bulk-batch/', views.custom_collections_report, name='bulk_batch_report'),

    # Settings
    path('organization/', views.organization_info, name='organization'),
    path('branches/', views.branches, name='branches'),
    path('officers/', views.loan_officers, name='loan_officers'),
    
    # Posting Batches
    path('posting-batches/', views.posting_batches, name='posting_batches'),
    path('posting-batches/create/', views.create_posting_batch, name='create_posting_batch'),
    path('posting-batches/<int:batch_id>/add-item/', views.add_posting_item, name='add_posting_item'),
    path('posting-batches/<int:pk>/', views.posting_batch_detail, name='posting_batch_detail'),
    # Custom date-range collections report
    # path('reports/custom/', views.custom_collections_report, name='custom_collections_report'),
    
    
    
    # EXPENSES
    path('vendors/', views.vendors_view, name='vendors'),
    path('vendors/add/', views.add_vendor, name='add_vendor'),
    path('expenses/', views.expenses_view, name='expenses'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path("expenses/update/<int:expense_id>/", views.update_expense, name="update_expense"),


    # ACCOUNTING
    path('accounting/profit-loss/', views.profit_loss, name='profit_loss'),
    path('accounting/trial-balance/', views.trial_balance, name='trial_balance'),
    path('accounting/branch-equity/', views.branch_equity, name='branch_equity'),
    
    path('reports/daily/', views.reports_daily_collections, name='reports_daily_collections'),
    path('reports/monthly/', views.reports_monthly_collections, name='reports_monthly_collections'),
    path('reports/custom/', views.reports_custom_collections, name='reports_custom_collections'),
    path('reports/profit-loss/', views.profit_loss, name='profit_loss'),
    path('reports/balance-sheet/', views.balance_sheet, name='balance_sheet'),
    path('reports/trial-balance/', views.trial_balance, name='trial_balance'),
    path('reports/branch-equity/', views.branch_equity, name='branch_equity'),
    path('reports/officer-performance/', views.reports_officer_performance, name='reports_officer_performance'),




    # Excel export URLs
    path('reports/balance-sheet/excel/', views.balance_sheet_excel, name='balance_sheet_excel'),
    path('reports/daily-collections/excel/', views.daily_collections_excel, name='daily_collections_excel'),
    path('reports/monthly-collections/excel/', views.monthly_collections_excel, name='monthly_collections_excel'),
    path('reports/custom-collections/excel/', views.custom_collections_excel, name='custom_collections_excel'),
    path('reports/officer-performance/excel/', views.officer_performance_excel, name='officer_performance_excel'),
    path('reports/par30-loans/excel/', views.par30_loans_excel, name='par30_loans_excel'),
    path('reports/profit-loss/excel/', views.profit_loss_excel, name='profit_loss_excel'),
    path('reports/trial-balance/excel/', views.trial_balance_excel, name='trial_balance_excel'),
    path('reports/branch-equity/excel/', views.branch_equity_excel, name='branch_equity_excel'),
    path('loans/excel/', views.loan_portfolio_excel, name='loan_portfolio_excel'),

]