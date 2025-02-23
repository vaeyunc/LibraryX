# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group, Permission
from .models import (
    Book, Category, BookBorrowing, BookReturn, 
    BookReservation, BookComment, BookRecommendation, 
    UserProfile, Notification, 
)

# 注册通知模型
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    ordering = ('-created_at',)
    
    # 添加自定义操作按钮
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'已将 {queryset.count()} 条通知标记为已读')
    mark_as_read.short_description = '标记为已读'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'已将 {queryset.count()} 条通知标记为未读')
    mark_as_unread.short_description = '标记为未读'
    
    def has_add_permission(self, request):
        # 允许添加通知
        return True
        
    def has_change_permission(self, request, obj=None):
        # 允许修改通知
        return True

# 注册权限模型
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'codename')
    list_filter = ('content_type',)
    search_fields = ('name', 'codename')

# 重新注册 User 模型
admin.site.unregister(User)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

# 重新注册 Group 模型
admin.site.unregister(Group)
@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    filter_horizontal = ('permissions',)

# 注册其他模型
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'isbn', 'available', 'quantity')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'author', 'isbn')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent')
    list_filter = ('parent',)
    search_fields = ('name', 'code')

@admin.register(BookBorrowing)
class BookBorrowingAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'borrowed_date', 'due_date', 'status', 'returned')
    list_filter = ('status', 'returned', 'borrowed_date')
    search_fields = ('book__title', 'borrower__username')

@admin.register(BookReturn)
class BookReturnAdmin(admin.ModelAdmin):
    list_display = ('book', 'returner', 'return_date', 'returned')
    list_filter = ('returned', 'return_date')
    search_fields = ('book__title', 'returner__username')

@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'reservationer', 'reservation_date', 'returned')
    list_filter = ('returned', 'reservation_date')
    search_fields = ('book__title', 'reservationer__username')

@admin.register(BookComment)
class BookCommentAdmin(admin.ModelAdmin):
    list_display = ('book', 'commenter', 'comment_date')
    list_filter = ('comment_date',)
    search_fields = ('book__title', 'commenter__username', 'comment')

@admin.register(BookRecommendation)
class BookRecommendationAdmin(admin.ModelAdmin):
    list_display = ('book', 'recommender', 'recommendation_date')
    list_filter = ('recommendation_date',)
    search_fields = ('book__title', 'recommender__username', 'reason')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'phone')
    search_fields = ('user__username', 'email', 'phone')
    
    