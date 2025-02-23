from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from books.models import Book, UserPermissions

class Command(BaseCommand):
    help = '初始化权限和用户组'

    def handle(self, *args, **options):
        # 获取 Book 模型的 content type
        book_content_type = ContentType.objects.get_for_model(Book)
        
        # 创建权限
        permissions = []
        for codename, name in UserPermissions.get_default_permissions():
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=book_content_type,
            )
            permissions.append(permission)
            if created:
                self.stdout.write(f'Created permission: {name}')
        
        # 创建管理权限
        staff_permissions = []
        for codename, name in UserPermissions.get_staff_permissions():
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=book_content_type,
            )
            staff_permissions.append(permission)
            if created:
                self.stdout.write(f'Created staff permission: {name}')
        
        # 创建用户组
        reader_group, created = Group.objects.get_or_create(name='读者')
        if created:
            self.stdout.write('Created group: 读者')
        reader_group.permissions.set(permissions)
        
        librarian_group, created = Group.objects.get_or_create(name='图书管理员')
        if created:
            self.stdout.write('Created group: 图书管理员')
        librarian_group.permissions.set(permissions + staff_permissions) 