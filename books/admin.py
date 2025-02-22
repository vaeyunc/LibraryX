# Register your models here.
from django.contrib import admin
from .models import Category, Book, BookBorrowing, BookReturn, BookReservation, BookComment, BookRecommendation

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent', 'description', 'created_at', 'update_at')
    list_filter = ('parent', 'created_at', 'update_at')
    search_fields = ('name', 'code', 'parent__name', 'parent__code')
    list_per_page = 8

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'isbn', 'quantity', 'available')
    list_filter = ('category', 'author')
    search_fields = ('title', 'author', 'isbn')
    list_per_page = 8

@admin.register(BookBorrowing)
class BookBorrowingAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'borrowed_date', 'return_date', 'returned')
    list_filter = ('returned', 'borrowed_date')
    search_fields = ('book__title', 'borrower__username')
    list_per_page = 8

@admin.register(BookReturn)
class BookReturnAdmin(admin.ModelAdmin):
    list_display = ('book', 'returner', 'return_date', 'returned')
    list_filter = ('returned', 'return_date')
    search_fields = ('book__title', 'returner__username')
    list_per_page = 8

@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'reservationer', 'reservation_date', 'returned')
    list_filter = ('returned', 'reservation_date')
    search_fields = ('book__title', 'reservationer__username')
    list_per_page = 8

@admin.register(BookComment)
class BookCommentAdmin(admin.ModelAdmin):
    list_display = ('book', 'commenter', 'comment_date', 'comment')
    list_filter = ('comment_date', 'commenter')
    search_fields = ('book__title', 'commenter__username')
    list_per_page = 8

@admin.register(BookRecommendation)
class BookRecommendationAdmin(admin.ModelAdmin):
    list_display = ('book', 'recommender', 'recommendation_date',)
    list_filter = ('recommendation_date',)
    search_fields = ('book__title', 'recommender__username')
    list_per_page = 8
    

    
    
    