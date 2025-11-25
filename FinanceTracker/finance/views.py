from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Expense, Income, Category, Budget
from .forms import ExpenseForm, IncomeForm, CategoryForm, BudgetForm, RegisterForm
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth import login
from datetime import datetime
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
 

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


@login_required
def dashboard(request):
    user = request.user

    # Month/year filter via GET (fallback to current month)
    try:
        selected_month = int(request.GET.get('month') or datetime.today().month)
        selected_year = int(request.GET.get('year') or datetime.today().year)
    except ValueError:
        selected_month = datetime.today().month
        selected_year = datetime.today().year

    # Filter user's expenses/income
    expenses_qs = Expense.objects.filter(user=user, date__year=selected_year, date__month=selected_month)
    incomes_qs = Income.objects.filter(user=user, date__year=selected_year, date__month=selected_month)

    total_expenses = expenses_qs.aggregate(total=Sum('amount'))['total'] or 0
    total_income = incomes_qs.aggregate(total=Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

    # breakdown by category (for chart)
    breakdown_qs = expenses_qs.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    breakdown = [{'category': item['category__name'] or 'Uncategorized', 'total': float(item['total'])} for item in breakdown_qs]

    # budgets for this user for the selected month + general budgets (year/month null)
    budget_qs = Budget.objects.filter(user=user).filter(models.Q(year=selected_year, month=selected_month) | models.Q(year__isnull=True, month__isnull=True))
    # But to avoid importing models.Q at top, use this simpler split:
    # We'll fetch both sets then combine
    from django.db.models import Q
    budgets = Budget.objects.filter(user=user).filter(Q(year=selected_year, month=selected_month) | Q(year__isnull=True, month__isnull=True))

    # prepare budgets data with spent
    budget_alerts = []
    budgets_list = []
    for b in budgets:
        spent = expenses_qs.filter(category=b.category).aggregate(total=Sum('amount'))['total'] or 0
        budgets_list.append({
            'id': b.id,
            'category': b.category,
            'limit': b.limit_amount,
            'spent': spent
        })
        if spent >= b.limit_amount:
            budget_alerts.append({
                'category': b.category.name,
                'limit': float(b.limit_amount),
                'spent': float(spent)
            })

    # recent items to show in lists (latest 50 overall, not only month)
    recent_expenses = Expense.objects.filter(user=user).order_by('-date')[:50]
    recent_incomes = Income.objects.filter(user=user).order_by('-date')[:50]
    categories = Category.objects.filter(user=user).order_by('name')

    context = {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'balance': balance,
        'breakdown': breakdown,
        'budget_alerts': budget_alerts,
        'budgets_list': budgets_list,
        'recent_expenses': recent_expenses,
        'recent_incomes': recent_incomes,
        'categories': categories,
        'selected_month': selected_month,
        'selected_year': selected_year,
        
    }
    return render(request, 'finance/dashboard.html', context)

# ---------- Expense CRUD ----------
@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    return render(request, 'expense_list.html', {'expenses': expenses})

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.user = request.user
            exp.save()
            messages.success(request, "Expense added.")
            return redirect('finance:expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'expense_form.html', {'form': form, 'title': 'Add Expense'})

@login_required
def edit_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=exp)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated.")
            return redirect('finance:expense_list')
    else:
        form = ExpenseForm(instance=exp)
    return render(request, 'expense_form.html', {'form': form, 'title': 'Edit Expense'})

@login_required
def delete_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        exp.delete()
        messages.success(request, "Expense deleted.")
        return redirect('finance:expense_list')
    return render(request, 'confirm_delete.html', {'object': exp})

# ---------- Income CRUD ----------
@login_required
def income_list(request):
    incomes = Income.objects.filter(user=request.user).order_by('-date')
    return render(request, 'income_list.html', {'incomes': incomes})

@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            inc = form.save(commit=False)
            inc.user = request.user
            inc.save()
            messages.success(request, "Income added.")
            return redirect('finance:income_list')
    else:
        form = IncomeForm()
    return render(request, 'income_form.html', {'form': form, 'title': 'Add Income'})

@login_required
def edit_income(request, pk):
    inc = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=inc)
        if form.is_valid():
            form.save()
            messages.success(request, "Income updated.")
            return redirect('finance:income_list')
    else:
        form = IncomeForm(instance=inc)
    return render(request, 'income_form.html', {'form': form, 'title': 'Edit Income'})

@login_required
def delete_income(request, pk):
    inc = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        inc.delete()
        messages.success(request, "Income deleted.")
        return redirect('finance:income_list')
    return render(request, 'confirm_delete.html', {'object': inc})

# ---------- Category CRUD ----------
@login_required
def category_list(request):
    cats = Category.objects.filter(user=request.user).order_by('name')
    return render(request, 'category_list.html', {'categories': cats})

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.user = request.user
            cat.save()
            messages.success(request, "Category added.")
            return redirect('finance:category_list')
    else:
        form = CategoryForm()
    return render(request, 'category_form.html', {'form': form, 'title': 'Add Category'})

@login_required
def edit_category(request, pk):
    cat = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect('finance:category_list')
    else:
        form = CategoryForm(instance=cat)
    return render(request, 'category_form.html', {'form': form, 'title': 'Edit Category'})

@login_required
def delete_category(request, pk):
    cat = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, "Category deleted.")
        return redirect('finance:category_list')
    return render(request, 'confirm_delete.html', {'object': cat})

# ---------- Budgets ----------
@login_required
def manage_budgets(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            b = form.save(commit=False)
            b.user = request.user
            b.save()
            messages.success(request, "Budget saved.")
            return redirect('finance:manage_budgets')
    else:
        form = BudgetForm()
    # compute spent for shown budgets (selected month)
    from django.db.models import Q
    try:
        selected_month = int(request.GET.get('month') or datetime.today().month)
        selected_year = int(request.GET.get('year') or datetime.today().year)
    except ValueError:
        selected_month = datetime.today().month
        selected_year = datetime.today().year

    budgets = Budget.objects.filter(user=request.user).order_by('-year', '-month', 'category__name')
    display_budgets = []
    for b in budgets:
        # spend for month if b has month/year else sum for that category in selected month
        if b.year and b.month:
            spent = Expense.objects.filter(user=request.user, category=b.category, date__year=b.year, date__month=b.month).aggregate(total=Sum('amount'))['total'] or 0
        else:
            spent = Expense.objects.filter(user=request.user, category=b.category, date__year=selected_year, date__month=selected_month).aggregate(total=Sum('amount'))['total'] or 0
        display_budgets.append({
            'id': b.id,
            'category': b.category,
            'limit': b.limit_amount,
            'spent': spent
        })
    return render(request, 'finance/budgets.html', {'form': form, 'budgets': display_budgets})
