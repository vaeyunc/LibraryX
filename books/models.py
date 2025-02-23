from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='分类名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='分类编码', null=True,blank=True )
    parent = models.ForeignKey('self', verbose_name='父级分类', null=True, blank=True, on_delete=models.CASCADE)
    description = models.TextField('描述', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', null=True, blank=True)
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_full_path(self):
        """获取完整的分类路径"""
        path = [self.name]
        current = self
        while current.parent:
            current = current.parent
            path.append(current.name)
        return ' > '.join(reversed(path))

    class Meta:
        db_table = 'books_category'
        verbose_name = "图书分类"
        verbose_name_plural = verbose_name      

class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name='图书名称')
    author = models.CharField(max_length=200, verbose_name='作者')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    isbn = models.CharField(max_length=13, unique=True, verbose_name='ISBN')
    quantity = models.IntegerField(default=1, verbose_name='数量')
    available = models.IntegerField(default=1, verbose_name='可用数量')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_at= models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return self.title

    def is_available(self):
        """检查图书是否可借"""
        return self.available > 0

    def can_reserve(self):
        """检查图书是否可以预约"""
        return self.available == 0 and self.quantity > 0

    def get_active_reservations(self):
        """获取当前有效的预约"""
        return self.bookreservation_set.filter(returned=False)

    def get_borrowing_history(self):
        """获取借阅历史"""
        return self.bookborrowing_set.all().order_by('-borrowed_date')

    class Meta:
        db_table = 'books_book'
        verbose_name = "图书"
        verbose_name_plural = verbose_name


class BookBorrowing(models.Model):
    STATUS_CHOICES = (
        ('borrowed', '借阅中'),
        ('returned', '已归还'),
        ('overdue', '已逾期'),
    )
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='图书')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='借阅者')
    borrowed_date = models.DateTimeField(auto_now_add=True, verbose_name='借阅时间')
    due_date = models.DateTimeField(null=True,blank=True,verbose_name='应还时间')
    return_date = models.DateTimeField(null=True, blank=True, verbose_name='归还时间')
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='borrowed',
        verbose_name='借阅状态'
    )
    returned = models.BooleanField(default=False, verbose_name='是否归还')

    def __str__(self):
        return f"{self.borrower.username} borrowed {self.book.title}"

    def save(self, *args, **kwargs):
        if self.returned:
            self.status = 'returned'
        elif self.due_date and self.due_date < timezone.now():
            self.status = 'overdue'
        else:
            self.status = 'borrowed'
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'books_bookborrowing'
        verbose_name = "借阅记录"
        verbose_name_plural = verbose_name

class BookReturn(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='图书')
    returner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='归还者')
    return_date = models.DateTimeField(auto_now_add=True, verbose_name='归还时间')
    returned = models.BooleanField(default=False, verbose_name='是否归还')

    def __str__(self):
        return f"{self.returner.username} returned {self.book.title}"
    
    class Meta:
        db_table = 'books_bookreturn'
        verbose_name = "归还记录"
        verbose_name_plural = verbose_name

class BookReservation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='图书')
    reservationer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='预约者')
    reservation_date = models.DateTimeField(auto_now_add=True, verbose_name='预约时间')
    returned = models.BooleanField(default=False, verbose_name='是否归还')
    
    def __str__(self):
        return f"{self.reservationer.username} reserved {self.book.title}"
    
    class Meta:
        db_table = 'books_bookreservation'
        verbose_name = "预约记录"
        verbose_name_plural = verbose_name

class BookComment(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='图书')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='评论者')
    comment_date = models.DateTimeField(auto_now_add=True, verbose_name='评论时间')
    comment = models.TextField(verbose_name='评论')
    
    def __str__(self):
        return f"{self.commenter.username} commented on {self.book.title}"
    
    class Meta: 
        db_table = 'books_bookcomment'
        verbose_name = "图书评论"
        verbose_name_plural = verbose_name

class BookRecommendation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='图书')
    recommender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='推荐者')
    recommendation_date = models.DateTimeField(auto_now_add=True, verbose_name='推荐时间')
    reason = models.TextField(verbose_name='推荐理由',blank=True)
    def __str__(self):
        return f"{self.recommender.username} recommended {self.book.title}"
    
    class Meta:
        db_table = 'books_bookrecommendation'
        verbose_name = "图书推荐"
        verbose_name_plural = verbose_name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')
    email = models.EmailField(verbose_name='邮箱')
    phone = models.CharField(max_length=11, verbose_name='电话')
    avatar = models.ImageField(upload_to='avatar/', verbose_name='头像', null=True, blank=True)

    def __str__(self):
        return self.user.username
    
    class Meta:
        db_table = 'books_userprofile'
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('borrow', '借阅提醒'),
        ('return', '归还提醒'),
        ('overdue', '逾期提醒'),
        ('reserve', '预约提醒'),
        ('system', '系统通知'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='接收者')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name='通知类型')
    title = models.CharField(max_length=200, verbose_name='通知标题')
    message = models.TextField(verbose_name='通知内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    related_book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='相关图书')
    
    class Meta:
        db_table = 'books_notification'
        verbose_name = "系统通知"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"

# 定义权限常量
class UserPermissions:
    BORROW_BOOK = 'borrow_book'
    RETURN_BOOK = 'return_book'
    RESERVE_BOOK = 'reserve_book'
    MANAGE_BOOKS = 'manage_books'
    MANAGE_USERS = 'manage_users'
    
    @classmethod
    def get_default_permissions(cls):
        return [
            (cls.BORROW_BOOK, '借阅图书'),
            (cls.RETURN_BOOK, '归还图书'),
            (cls.RESERVE_BOOK, '预约图书'),
        ]
    
    @classmethod
    def get_staff_permissions(cls):
        return [
            (cls.MANAGE_BOOKS, '管理图书'),
            (cls.MANAGE_USERS, '管理用户'),
        ]
        




