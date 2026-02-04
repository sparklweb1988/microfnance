from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from datetime import date
from datetime import timedelta
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.contrib.auth.models import User
from .models import (
    Borrower, Loan, Repayment,
    PostingBatch, PostingItem,
    Branch, LoanOfficer,
    CollectionSheet, 
    CollectionItem,
    Vendor,
    Expense,
    Expense, Branch, 
   
    
  
)
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from django.http import HttpResponse
import pandas as pd
import openpyxl










@login_required
def dashboard(request):
    organization = request.user.loanofficer.organization

    # Counts
    borrowers_count = Borrower.objects.filter(organization=organization).count()
    loans_count = Loan.objects.filter(organization=organization).count()
    active_loans = Loan.objects.filter(organization=organization, status='Active').count()
    overdue_loans = Loan.objects.filter(organization=organization, status='Overdue').count()
    par30_loans = Loan.objects.filter(organization=organization, status='PAR30').count()
    closed_loans = Loan.objects.filter(organization=organization, status='Closed').count()

    # Total portfolio
    total_portfolio = Loan.objects.filter(organization=organization).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('principal') + (F('principal') * F('interest_rate') / 100),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
    )['total'] or 0

    # Total repayments
    total_repayments = Repayment.objects.filter(
        loan__organization=organization
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Total savings
    total_savings = Saving.objects.filter(
        organization=organization
    ).aggregate(total=Sum('ledger_balance'))['total'] or 0

    # Total collections (sum amounts in CollectionItem linked to organization loans)
    total_collections = CollectionItem.objects.filter(
        loan__organization=organization
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Chart.js data for last 6 months
    today = now().date()
    six_months_ago = today - timedelta(days=180)

    monthly_data = (
        Repayment.objects
        .filter(loan__organization=organization, date__gte=six_months_ago)
        .annotate(month=F('date__month'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    chart_labels = [f"Month {d['month']}" for d in monthly_data]
    chart_values = [float(d['total']) for d in monthly_data]

    context = {
        'borrowers': borrowers_count,
        'loans': loans_count,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'par30': par30_loans,
        'closed_loans': closed_loans,
        'total_portfolio': total_portfolio,
        'total_repayments': total_repayments,
        'total_collections': total_collections,
        'total_savings': total_savings,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    }

    return render(request, 'dashboard.html', context)

# -------------------------
# BORROWERS
# -------------------------

# core/views.py


@login_required
def borrowers_view(request):
    organization = request.user.loanofficer.organization
    borrowers = Borrower.objects.filter(organization=organization)
    return render(request, 'borrowers.html', {'borrowers': borrowers})




@login_required
def add_borrower(request):
    organization = request.user.loanofficer.organization
    branches = Branch.objects.filter(organization=organization)

    if request.method == "POST":
        Borrower.objects.create(
            organization=organization,
            branch_id=request.POST.get("branch"),
            full_name=request.POST.get("full_name"),
            business=request.POST.get("business"),
            unique_id=request.POST.get("unique_id"),
            mobile=request.POST.get("mobile"),
            email=request.POST.get("email"),
            status=request.POST.get("status"),
        )
        return redirect("/borrowers/")

    return render(request, "add_borrowers.html", {"branches": branches})

# -------------------------
# LOANS
# -------------------------


@login_required
def loans_view(request):
    organization = request.user.loanofficer.organization
    loans = Loan.objects.filter(organization=organization)
    borrowers = Borrower.objects.filter(organization=organization)
    branches = organization.branch_set.all()
    return render(request, 'loans.html', {'loans': loans, 'borrowers': borrowers, 'branches': branches})





from decimal import Decimal

@login_required
def add_loan(request):
    organization = request.user.loanofficer.organization
    borrowers = Borrower.objects.filter(organization=organization)
    branches = Branch.objects.filter(organization=organization)

    if request.method == "POST":
        # Convert strings to Decimal for safe calculation
        principal = Decimal(request.POST.get("principal"))
        interest_rate = Decimal(request.POST.get("interest_rate"))
        tenure = int(request.POST.get("tenure"))

        # Create a new loan
        Loan.objects.create(
            organization=organization,
            branch_id=request.POST.get("branch"),
            borrower_id=request.POST.get("borrower"),
            principal=principal,
            interest_rate=interest_rate,
            tenure=tenure,
            status="Active",
        )
        return redirect("/loans/")

    return render(request, "add_loan.html", {
        "borrowers": borrowers,
        "branches": branches
    })



@login_required
def overdue_loans(request):
    # Get organization of logged-in loan officer
    organization = request.user.loanofficer.organization

    # Filter loans that are overdue for this organization
    loans = Loan.objects.filter(
        organization=organization,
        status='Overdue'
    )

    return render(request, 'overdue_loans.html', {'loans': loans})


# -------------------------
# REPAYMENTS
# -------------------------
@login_required
def repayments_view(request):
    organization = request.user.loanofficer.organization
    repayments = Repayment.objects.filter(loan__organization=organization)
    return render(request, 'repayments.html', {'repayments': repayments})




@login_required
def add_repayment(request):
    organization = request.user.loanofficer.organization
    loans = Loan.objects.filter(organization=organization)

    if request.method == "POST":
        loan_id = request.POST.get("loan")
        amount = request.POST.get("amount")
        loan = Loan.objects.get(id=loan_id)
        
        Repayment.objects.create(
            loan=loan,
            amount=amount,
            posted_by=request.user
        )
        return redirect('repayments')

    return render(request, 'add_repayment.html', {'loans': loans})

# -------------------------
# POSTING BATCHES
# -------------------------



@login_required
def posting_batches(request):
    organization = request.user.loanofficer.organization
    batches = PostingBatch.objects.filter(officer__organization=organization)
    return render(request, 'posting_batches.html', {'batches': batches})




@login_required
def posting_batch_detail(request, pk):
    organization = request.user.loanofficer.organization
    batch = get_object_or_404(PostingBatch, pk=pk, officer__organization=organization)
    items = PostingItem.objects.filter(batch=batch)
    return render(request, 'posting_batch_detail.html', {'batch': batch, 'items': items})






@login_required
def create_posting_batch(request):
    if request.method == "POST":
        batch = PostingBatch.objects.create(
            officer=request.user.loanofficer,
            date=request.POST.get("date")
        )
        return redirect("posting_batch_detail", pk=batch.id)
    return render(request, "create_posting_batch.html")



@login_required
def add_posting_item(request, batch_id):
    batch = PostingBatch.objects.get(pk=batch_id)
    loans = Loan.objects.filter(organization=request.user.loanofficer.organization)
    
    if request.method == "POST":
        loan_id = request.POST.get("loan")
        amount = request.POST.get("amount")
        remarks = request.POST.get("remarks", "")
        loan = Loan.objects.get(pk=loan_id)
        PostingItem.objects.create(
            batch=batch,
            loan=loan,
            amount=amount,
            remarks=remarks
        )
        return redirect("posting_batch_detail", pk=batch.id)

    return render(request, "add_posting_item.html", {"batch": batch, "loans": loans})






@login_required
def officer_performance(request):
    organization = request.user.loanofficer.organization

    performance = Loan.objects.filter(
        organization=organization
    ).values(
        'officer__user__username'
    ).annotate(
        portfolio=Sum(
            ExpressionWrapper(
                F('principal') + (F('principal') * F('interest_rate') / 100),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
    )

    return render(request, 'officer_performance.html', {'performance': performance})


# -------------------------
# SETTINGS
# -------------------------
@login_required
def organization_info(request):
    organization = request.user.loanofficer.organization
    return render(request, 'organization_info.html', {
        'organization': organization
    })





# BRANCHES
# -------------------------

# -------- BRANCHES --------
@login_required
def branches(request):
    branches = Branch.objects.filter(organization=request.user.loanofficer.organization)
    
    if request.method == "POST":
        Branch.objects.create(
            organization=request.user.loanofficer.organization,
            name=request.POST.get("name")
        )
        return redirect("branches")
    
    return render(request, "branches.html", {"branches": branches})



# -------- LOAN OFFICERS --------
@login_required
def loan_officers(request):
    branches = Branch.objects.filter(organization=request.user.loanofficer.organization)
    officers = LoanOfficer.objects.filter(organization=request.user.loanofficer.organization)
    
    if request.method == "POST":
        user = User.objects.create_user(
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )
        LoanOfficer.objects.create(
            user=user,
            organization=request.user.loanofficer.organization,
            branch_id=request.POST.get("branch")
        )
        return redirect("loan_officers")
    
    return render(request, "loan_officers.html", {"branches": branches, "officers": officers})




@login_required
def par30_loans(request):
    organization = request.user.loanofficer.organization
    # Example: loans overdue by 30 days
    loans = Loan.objects.filter(
        organization=organization,
        status='PAR30'  # or your logic for 30 days overdue
    )
    return render(request, 'par30_loans.html', {'loans': loans})










from .models import Saving

@login_required
def savings_view(request):
    organization = request.user.loanofficer.organization
    savings = Saving.objects.filter(organization=organization)
    borrowers = Borrower.objects.filter(organization=organization)
    return render(request, 'savings.html', {'savings': savings, 'borrowers': borrowers})



from decimal import Decimal
from django.db.models import Sum





@login_required
def add_saving(request):
    organization = request.user.loanofficer.organization
    borrowers = Borrower.objects.filter(organization=organization)

    if request.method == "POST":
        borrower_id = request.POST.get("borrower")
        product = request.POST.get("product")
        name = request.POST.get("name")
        account_number = request.POST.get("account_number")
        status = request.POST.get("status")
        deposit_amount = Decimal(request.POST.get("deposit_amount", '0.00'))

        borrower = Borrower.objects.get(id=borrower_id)

        # Sum previous ledger balance for this borrower
        previous_balance = Saving.objects.filter(borrower=borrower).aggregate(
            total=Sum('ledger_balance')
        )['total'] or Decimal('0.00')

        # New ledger balance
        new_ledger_balance = previous_balance + deposit_amount

        Saving.objects.create(
            organization=organization,
            borrower=borrower,
            name=name,
            account_number=account_number,
            product=product,
            ledger_balance=new_ledger_balance,
            last_transaction=now().date(),
            status=status
        )

        return redirect('/savings/')

    return render(request, 'add_saving.html', {
        'borrowers': borrowers
    })
    
    
    


@login_required
def collection_sheet(request):
    organization = request.user.loanofficer.organization

    # Fetch loans for dropdown
    loans = Loan.objects.filter(organization=organization)

    # Handle POST (add collection)
    if request.method == "POST":
        loan_id = request.POST.get("loan")
        amount = request.POST.get("amount")
        date = request.POST.get("date")

        loan = Loan.objects.get(id=loan_id)
        Repayment.objects.create(
            loan=loan,
            amount=amount,
            date=date,
            posted_by=request.user
        )

        # Update loan's paid field automatically
        loan.paid = sum(r.amount for r in loan.repayments.all())
        loan.save()

        return redirect("collection_sheet")

    # Fetch all repayments for the organization
    collections = Repayment.objects.filter(loan__organization=organization).order_by("-date")

    return render(request, "collection_sheet.html", {
        "collections": collections,
        "loans": loans
    })
    
    
    
    


# DAILY COLLECTIONS
from django.utils.timezone import localdate

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date


@login_required
def daily_collections_report(request):
    today = date.today()

    collections = Repayment.objects.filter(
        loan__organization=request.user.loanofficer.organization,
        date=today
    ).select_related('loan', 'loan__borrower')

    total_collected = collections.aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(request, 'daily_collections.html', {
        'collections': collections,
        'total_collected': total_collected,
        'report_date': today
    })






# ---------------------------
# Daily Collections
# ---------------------------
@login_required
def reports_daily_collections(request):
    today = date.today()
    collections = Repayment.objects.filter(
        loan__organization=request.user.loanofficer.organization,
        date=today
    ).select_related('loan', 'loan__borrower')
    total_collected = collections.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'daily_collections.html', {
        'collections': collections,
        'total_collected': total_collected,
        'report_date': today
    })

# ---------------------------
# Monthly Collections
# ---------------------------
@login_required
def reports_monthly_collections(request):
    today = date.today()
    first_day_of_month = today.replace(day=1)
    collections = Repayment.objects.filter(
        loan__organization=request.user.loanofficer.organization,
        date__gte=first_day_of_month,
        date__lte=today
    ).select_related('loan', 'loan__borrower')
    total_collected = collections.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'monthly_collections.html', {
        'collections': collections,
        'total_collected': total_collected,
        'start_date': first_day_of_month,
        'end_date': today
    })

# ---------------------------
# Custom Collections
# ---------------------------
@login_required
def reports_custom_collections(request):
    organization = request.user.loanofficer.organization
    collections = []
    total_collected = 0
    start_date = end_date = None

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date and end_date:
            collections = Repayment.objects.filter(
                loan__organization=organization,
                date__gte=start_date,
                date__lte=end_date
            ).select_related('loan', 'loan__borrower')
            total_collected = collections.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'custom_collections.html', {
        'collections': collections,
        'total_collected': total_collected,
        'start_date': start_date,
        'end_date': end_date
    })

# ---------------------------
# Officer Performance
# ---------------------------
@login_required
def reports_officer_performance(request):
    organization = request.user.loanofficer.organization
    performance = Loan.objects.filter(
        organization=organization
    ).values('officer__user__username').annotate(
        portfolio=Sum(
            ExpressionWrapper(
                F('principal') + (F('principal') * F('interest_rate') / 100),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
    )
    return render(request, 'officer_performance.html', {'performance': performance})



# # MONTHLY COLLECTIONS
# @login_required
# def monthly_collections_report(request):
#     today = now().date()
#     first_day = today.replace(day=1)

#     collections = Repayment.objects.filter(
#         loan__organization=request.user.loanofficer.organization,
#         date__gte=first_day,
#         date__lte=today
#     ).select_related('loan', 'loan__borrower')

#     total_collected = collections.aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'monthly_collections.html', {
#         'collections': collections,
#         'total_collected': total_collected,
#         'start_date': first_day,
#         'end_date': today
#     })
    
    
    



# @login_required
# def custom_collections_report(request):
#     organization = request.user.loanofficer.organization
#     collections = []
#     total_collected = 0
#     start_date = end_date = None

#     if request.method == "POST":
#         start_date = request.POST.get('start_date')
#         end_date = request.POST.get('end_date')

#         if start_date and end_date:
#             collections = Repayment.objects.filter(
#                 loan__organization=organization,
#                 date__gte=start_date,
#                 date__lte=end_date
#             ).select_related('loan', 'loan__borrower')

#             total_collected = collections.aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'custom_collections.html', {
#         'collections': collections,
#         'total_collected': total_collected,
#         'start_date': start_date,
#         'end_date': end_date
#     })
    




@login_required
def posting_batches(request):
    organization = request.user.loanofficer.organization
    batches = PostingBatch.objects.filter(officer__organization=organization)
    return render(request, 'posting_batches.html', {'batches': batches})





@login_required
def posting_batch_detail(request, pk):
    batch = get_object_or_404(PostingBatch, pk=pk, officer__organization=request.user.loanofficer.organization)
    items = batch.items.all()  # Use the related_name
    return render(request, 'posting_batch_detail.html', {'batch': batch, 'items': items})




@login_required
def vendors_view(request):
    vendors = Vendor.objects.filter(
        organization=request.user.loanofficer.organization
    )
    return render(request, 'vendors.html', {'vendors': vendors})






@login_required
def add_vendor(request):
    if request.method == "POST":
        Vendor.objects.create(
            organization=request.user.loanofficer.organization,
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            email=request.POST.get("email"),
        )
        return redirect("vendors")

    return render(request, "add_vendor.html")





@login_required
def expenses_view(request):
    organization = request.user.loanofficer.organization
    expenses = Expense.objects.filter(organization=organization).select_related('branch', 'vendor')
    return render(request, "expenses.html", {'expenses': expenses})






@login_required
def add_expense(request):
    organization = request.user.loanofficer.organization
    branches = Branch.objects.filter(organization=organization)
    vendors = Vendor.objects.filter(organization=organization)

    if request.method == "POST":
        Expense.objects.create(
            organization=organization,
            branch_id=request.POST.get("branch"),
            vendor_id=request.POST.get("vendor"),
            category=request.POST.get("category"),
            amount=request.POST.get("amount"),
            description=request.POST.get("description"),
            recorded_by=request.user
        )
        return redirect("expenses")

    return render(request, "add_expense.html", {
        'branches': branches,
        'vendors': vendors
    })






@login_required
def profit_loss(request):
    organization = request.user.loanofficer.organization

    income = Repayment.objects.filter(
        loan__organization=organization
    ).aggregate(total=Sum('amount'))['total'] or 0

    expenses = Expense.objects.filter(
        organization=organization
    ).aggregate(total=Sum('amount'))['total'] or 0

    profit = income - expenses

    return render(request, "profit_loss.html", {
        'income': income,
        'expenses': expenses,
        'profit': profit
    })







@login_required
def trial_balance(request):
    organization = request.user.loanofficer.organization

    total_loans = Loan.objects.filter(
        organization=organization
    ).aggregate(total=Sum('principal'))['total'] or 0

    total_savings = Saving.objects.filter(
        organization=organization
    ).aggregate(total=Sum('ledger_balance'))['total'] or 0

    total_expenses = Expense.objects.filter(
        organization=organization
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, "trial_balance.html", {
        'loans': total_loans,
        'savings': total_savings,
        'expenses': total_expenses
    })









@login_required
def branch_equity(request):
    organization = request.user.loanofficer.organization
    branches = Branch.objects.filter(organization=organization)

    data = []

    for branch in branches:
        collections = Repayment.objects.filter(
            loan__branch=branch
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        expenses = Expense.objects.filter(
            branch=branch
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        equity = collections - expenses

        data.append({
            "branch": branch,
            "collections": collections,
            "expenses": expenses,
            "equity": equity
        })

    return render(request, "branch_equity.html", {"data": data})







EXPENSE_CATEGORIES = [
    "Rent",
    "Salary",
    "Fuel",
    "Utilities",
    "Maintenance",
    "Other",
]

@login_required
def update_expense(request, expense_id):
    organization = request.user.loanofficer.organization
    expense = get_object_or_404(Expense, id=expense_id, organization=organization)

    vendors = Vendor.objects.filter(organization=organization)
    branches = Branch.objects.filter(organization=organization)

    if request.method == "POST":
        expense.vendor_id = request.POST.get("vendor")
        expense.branch_id = request.POST.get("branch")
        expense.category = request.POST.get("category")
        expense.amount = request.POST.get("amount")
        expense.description = request.POST.get("description")
        expense.date = request.POST.get("date")
        expense.recorded_by = request.user
        expense.save()
        return redirect("expenses")

    return render(request, "update_expense.html", {
        "expense": expense,
        "vendors": vendors,
        "branches": branches,
        "categories": EXPENSE_CATEGORIES,
    })









# Collections Reports
# def reports_daily_collections(request):
  
#     return render(request, 'daily_collections.html')

# def reports_monthly_collections(request):
#     return render(request, 'monthly_collections.html')

# def reports_custom_collections(request):
#     return render(request, 'custom_collections.html')


# def profit_loss(request):
#     return render(request, 'profit_loss.html')

def balance_sheet(request):
    return render(request, 'balance_sheet.html')




from decimal import Decimal
from django.db.models import Sum
from .models import Loan, Saving, Expense

@login_required
def balance_sheet(request):
    organization = request.user.loanofficer.organization

    total_loans = Loan.objects.filter(
        organization=organization
    ).aggregate(total=Sum('principal'))['total'] or Decimal('0.00')

    total_savings = Saving.objects.filter(
        organization=organization
    ).aggregate(total=Sum('ledger_balance'))['total'] or Decimal('0.00')

    total_expenses = Expense.objects.filter(
        organization=organization
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    assets = total_loans + total_savings
    liabilities = total_expenses
    equity = assets - liabilities

    context = {
        'total_loans': total_loans,
        'total_savings': total_savings,
        'total_expenses': total_expenses,
        'assets': assets,
        'liabilities': liabilities,
        'equity': equity
    }

    return render(request, 'balance_sheet.html', context)


# def trial_balance(request):
#     return render(request, 'trial_balance.html')

# def branch_equity(request):
#     return render(request, 'branch_equity.html')


# def reports_officer_performance(request):
#     return render(request, 'officer_performance.html')


# def par30_loans(request):
#     return render(request, 'par30_loans.html')








# --------------------
# Collections Reports
# --------------------
@login_required
def daily_collections_excel(request):
    org = request.user.loanofficer.organization
    today_date = date.today()
    qs = Repayment.objects.filter(loan__organization=org, date=today_date).select_related('loan', 'loan__borrower')
    data = [{
        "Borrower": r.loan.borrower.full_name,
        "Loan ID": r.loan.id,
        "Amount": float(r.amount),
        "Date": r.date,
    } for r in qs]
    columns = ["Borrower", "Loan ID", "Amount", "Date"]
    return export_to_excel(data, columns, "daily_collections.xlsx")


@login_required
def monthly_collections_excel(request):
    org = request.user.loanofficer.organization
    today_date = date.today()
    first_day = today_date.replace(day=1)
    qs = Repayment.objects.filter(
        loan__organization=org,
        date__gte=first_day,
        date__lte=today_date
    ).select_related('loan', 'loan__borrower')
    data = [{
        "Borrower": r.loan.borrower.full_name,
        "Loan ID": r.loan.id,
        "Amount": float(r.amount),
        "Date": r.date,
    } for r in qs]
    columns = ["Borrower", "Loan ID", "Amount", "Date"]
    return export_to_excel(data, columns, "monthly_collections.xlsx")


@login_required
def custom_collections_excel(request):
    org = request.user.loanofficer.organization
    data = []
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        qs = Repayment.objects.filter(
            loan__organization=org,
            date__gte=start_date,
            date__lte=end_date
        ).select_related('loan', 'loan__borrower')
        data = [{
            "Borrower": r.loan.borrower.full_name,
            "Loan ID": r.loan.id,
            "Amount": float(r.amount),
            "Date": r.date,
        } for r in qs]

    columns = ["Borrower", "Loan ID", "Amount", "Date"]
    return export_to_excel(data, columns, "custom_collections.xlsx")


# --------------------
# Loans Reports
# --------------------
@login_required
def loan_portfolio_excel(request):
    org = request.user.loanofficer.organization
    qs = Loan.objects.filter(organization=org).select_related('borrower', 'branch', 'officer')
    data = [{
        "Borrower": l.borrower.full_name if l.borrower else "",
        "Loan ID": l.id,
        "Principal": float(l.principal),
        "Interest Rate": float(l.interest_rate),
        "Status": l.status,
        "Branch": l.branch.name if l.branch else "",
        "Officer": l.officer.user.username if l.officer else "",
    } for l in qs]
    columns = ["Borrower", "Loan ID", "Principal", "Interest Rate", "Status", "Branch", "Officer"]
    return export_to_excel(data, columns, "loan_portfolio.xlsx")


@login_required
def par30_loans_excel(request):
    org = request.user.loanofficer.organization
    qs = Loan.objects.filter(organization=org, status='PAR30').select_related('borrower', 'branch', 'officer')
    data = [{
        "Borrower": l.borrower.full_name if l.borrower else "",
        "Loan ID": l.id,
        "Principal": float(l.principal),
        "Balance": float(l.balance),
        "Branch": l.branch.name if l.branch else "",
        "Officer": l.officer.user.username if l.officer else "",
    } for l in qs]
    columns = ["Borrower", "Loan ID", "Principal", "Balance", "Branch", "Officer"]
    return export_to_excel(data, columns, "par30_loans.xlsx")


# --------------------
# Accounting Reports
# --------------------
@login_required
def profit_loss_excel(request):
    org = request.user.loanofficer.organization
    income = Repayment.objects.filter(loan__organization=org).aggregate(total=Sum('amount'))['total'] or 0
    expenses = Expense.objects.filter(organization=org).aggregate(total=Sum('amount'))['total'] or 0
    data = [{"Income": float(income), "Expenses": float(expenses), "Profit": float(income-expenses)}]
    columns = ["Income", "Expenses", "Profit"]
    return export_to_excel(data, columns, "profit_loss.xlsx")


@login_required
def balance_sheet_excel(request):
    org = request.user.loanofficer.organization
    total_loans = Loan.objects.filter(organization=org).aggregate(total=Sum('principal'))['total'] or 0
    total_savings = Saving.objects.filter(organization=org).aggregate(total=Sum('ledger_balance'))['total'] or 0
    total_expenses = Expense.objects.filter(organization=org).aggregate(total=Sum('amount'))['total'] or 0
    data = [{"Loans": float(total_loans), "Savings": float(total_savings), "Expenses": float(total_expenses)}]
    columns = ["Loans", "Savings", "Expenses"]
    return export_to_excel(data, columns, "balance_sheet.xlsx")


@login_required
def trial_balance_excel(request):
    org = request.user.loanofficer.organization
    total_loans = Loan.objects.filter(organization=org).aggregate(total=Sum('principal'))['total'] or 0
    total_savings = Saving.objects.filter(organization=org).aggregate(total=Sum('ledger_balance'))['total'] or 0
    total_expenses = Expense.objects.filter(organization=org).aggregate(total=Sum('amount'))['total'] or 0
    data = [{"Loans": float(total_loans), "Savings": float(total_savings), "Expenses": float(total_expenses)}]
    columns = ["Loans", "Savings", "Expenses"]
    return export_to_excel(data, columns, "trial_balance.xlsx")


@login_required
def branch_equity_excel(request):
    org = request.user.loanofficer.organization
    branches = Branch.objects.filter(organization=org)
    data = []
    for branch in branches:
        collections = Repayment.objects.filter(loan__branch=branch).aggregate(total=Sum("amount"))["total"] or 0
        expenses = Expense.objects.filter(branch=branch).aggregate(total=Sum("amount"))["total"] or 0
        data.append({
            "Branch": branch.name,
            "Collections": float(collections),
            "Expenses": float(expenses),
            "Equity": float(collections - expenses),
        })
    columns = ["Branch", "Collections", "Expenses", "Equity"]
    return export_to_excel(data, columns, "branch_equity.xlsx")


# --------------------
# Officer Performance
# --------------------
@login_required
def officer_performance_excel(request):
    org = request.user.loanofficer.organization
    qs = Loan.objects.filter(organization=org).values('officer__user__username').annotate(
        portfolio=Sum(F('principal') + F('principal') * F('interest_rate') / 100)
    )
    data = [{"Officer": r['officer__user__username'], "Portfolio": float(r['portfolio'] or 0)} for r in qs]
    columns = ["Officer", "Portfolio"]
    return export_to_excel(data, columns, "officer_performance.xlsx")

