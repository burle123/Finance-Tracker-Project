from django.contrib import admin
from .models import Category, Expense, Income, Budget

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'date', 'user', 'category')
    list_filter = ('date', 'category', 'user')
    search_fields = ('title', 'notes')

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'date', 'user')
    list_filter = ('date', 'user')
    search_fields = ('title', 'notes')

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'month', 'year', 'limit_amount')
    search_fields = ('category__name', 'user__username')
