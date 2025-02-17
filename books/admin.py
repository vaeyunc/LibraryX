from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Category, Book, BookBorrowing

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'isbn', 'quantity', 'available')
    list_filter = ('category', 'author')
    search_fields = ('title', 'author', 'isbn')

@admin.register(BookBorrowing)
class BookBorrowingAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'borrowed_date', 'return_date', 'returned')
    list_filter = ('returned', 'borrowed_date')
    search_fields = ('book__title', 'borrower__username')
    