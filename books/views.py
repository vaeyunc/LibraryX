from django.shortcuts import render, get_list_or_404, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.utils import timezone
from .models import Book, BookBorrowing, Category, BookReservation, Notification
from .forms import BookSearchForm, RegisterForm, BorrowingForm, UserProfileForm
from django.db.models import Count, F, Q
from datetime import timedelta



@login_required
def book_list(request):
    """图书列表视图"""
    books = Book.objects.all()
    form = BookSearchForm(request.GET)
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        category = form.cleaned_data.get('category')
        available_only = form.cleaned_data.get('available_only')
        
        if search_query:
            books = books.filter(
                Q(title__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(isbn__icontains=search_query)
            )
        
        if category:
            books = books.filter(category=category)
            
        if available_only:
            books = books.filter(available__gt=0)
    
    context = {
        'books': books,
        'form': form,
    }
    return render(request, 'books/book_list.html', context)

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    context = {
        'book': book,
    }
    return render(request, 'books/book_detail.html', context)

@login_required
@permission_required('books.borrow_book', raise_exception=True)
def borrow_book(request, pk):
    """借书视图"""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BorrowingForm(request.POST)
        if form.is_valid() and book.available > 0:
            borrowing = form.save(commit=False)
            borrowing.book = book
            borrowing.borrower = request.user
            
            # 设置到期时间和状态
            due_date = timezone.now() + timezone.timedelta(days=30)  # 默认借期30天
            borrowing.due_date = due_date
            borrowing.status = 'borrowed'
            borrowing.save()
            
            book.available -= 1
            book.save()
            
            # 创建借阅通知
            create_notification(
                user=request.user,
                notification_type='borrow',
                title=f'成功借阅《{book.title}》',
                message=f'您已成功借阅《{book.title}》，请在 {due_date.strftime("%Y-%m-%d")} 前归还。',
                related_book=book
            )
            
            messages.success(request, f'成功借阅《{book.title}》')
            return redirect('book_detail', pk=pk)
    else:
        form = BorrowingForm()
    
    context = {
        'book': book,
        'form': form,
    }
    return render(request, 'books/borrow_book.html', context)

@login_required
@permission_required('books.return_book', raise_exception=True)
def return_book(request, pk):
    """还书视图"""
    borrowing = get_object_or_404(
        BookBorrowing,
        book_id=pk,
        borrower=request.user,
        returned=False
    )
    
    # 检查是否逾期
    if borrowing.due_date and borrowing.due_date < timezone.now():
        create_notification(
            user=request.user,
            notification_type='overdue',
            title='图书逾期提醒',
            message=f'您归还的《{borrowing.book.title}》已逾期，请注意按时还书。',
            related_book=borrowing.book
        )
    else:
        create_notification(
            user=request.user,
            notification_type='return',
            title='图书归还成功',
            message=f'您已成功归还《{borrowing.book.title}》，欢迎下次借阅。',
            related_book=borrowing.book
        )
    
    borrowing.returned = True
    borrowing.return_date = timezone.now()
    borrowing.status = 'returned'
    borrowing.save()

    book = borrowing.book
    book.available += 1
    book.save()

    messages.success(request, f'您已成功归还《{book.title}》')
    return redirect('book_detail', pk=pk)

@login_required
def my_borrowings(request):
    borrowings = BookBorrowing.objects.filter(borrower=request.user).order_by('-borrowed_date')
    return render(request, 'accounts/my_borrowings.html', {'borrowings':borrowings})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 添加到读者组
            reader_group = Group.objects.get(name='读者')
            user.groups.add(reader_group)
            login(request, user)
            messages.success(request, '注册成功！')
            return redirect('book_list')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def index(request):
    #get some datas
    total_books = Book.objects.count() #int
    total_categories = Category.objects.count() #int
    recent_books = Book.objects.order_by('-id')[:6] # recent added six books
    popular_categories = Category.objects.annotate(
        book_count=Count('book')
    ).order_by('-book_count')[:5] # most popular five categories

    context = {
        'total_books': total_books,
        'total_categories': total_categories,
        'recent_books': recent_books,
        'popular_categories': popular_categories,
    }
    return render(request, 'index.html', context)

def library_status(request):
    #获取图书统计信息
    total_books = Book.objects.count()
    available_books = Book.objects.filter(available__gt=0).count()
    borrow_books = Book.objects.filter(available__lt=F('quantity')).count()

    #获取各分类图书数量
    categories = Category.objects.annotate(
        book_count=Count('book'),
        available_count=Count('book', filter=Q(book__available__gt=0))
    ).order_by('-book_count')

    #获取借阅量最多的图书
    popular_books = Book.objects.annotate(
        borrow_count=Count('bookborrowing')
    ).order_by('-borrow_count')[:5]

    #获取借阅统计信息
    borrow_stats = BookBorrowing.objects.values('book_id').annotate(
        borrow_count=Count('id')
    ).order_by('-borrow_count')

    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrow_books': borrow_books,
        'categories': categories,
        'popular_books': popular_books,
        'borrow_stats': borrow_stats,
    }
    return render(request, 'books/library_stats.html', context)
    
@login_required
def statistics_view(request):
    """统计视图"""
    # 获取时间范围
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # 图书统计
    book_stats = {
        'total_books': Book.objects.count(),
        'total_categories': Category.objects.count(),
        'available_books': Book.objects.filter(available__gt=0).count(),
        'borrowed_books': Book.objects.filter(available__lt=F('quantity')).count(),
    }
    
    # 借阅统计
    borrow_stats = {
        'total_borrowings': BookBorrowing.objects.count(),
        'active_borrowings': BookBorrowing.objects.filter(status='borrowed').count(),
        'overdue_borrowings': BookBorrowing.objects.filter(status='overdue').count(),
        'monthly_borrowings': BookBorrowing.objects.filter(
            borrowed_date__date__gte=last_30_days
        ).count(),
    }
    
    # 分类借阅排行
    category_stats = Category.objects.annotate(
        borrow_count=Count('book__bookborrowing')
    ).order_by('-borrow_count')[:5]
    
    # 热门图书排行
    popular_books = Book.objects.annotate(
        borrow_count=Count('bookborrowing')
    ).order_by('-borrow_count')[:5]
    
    # 活跃读者排行
    active_readers = User.objects.annotate(
        borrow_count=Count('bookborrowing')
    ).order_by('-borrow_count')[:5]

    context = {
        'book_stats': book_stats,
        'borrow_stats': borrow_stats,
        'category_stats': category_stats,
        'popular_books': popular_books,
        'active_readers': active_readers,
    }
    return render(request, 'books/statistics.html', context)

@login_required
def profile_view(request):
    """个人中心视图"""
    # 获取用户借阅统计
    user_stats = {
        'total_borrowed': BookBorrowing.objects.filter(borrower=request.user).count(),
        'current_borrowed': BookBorrowing.objects.filter(
            borrower=request.user,
            status='borrowed'
        ).count(),
        'overdue_books': BookBorrowing.objects.filter(
            borrower=request.user,
            status='overdue'
        ).count()
    }
    
    # 获取当前借阅
    current_borrowings = BookBorrowing.objects.filter(
        borrower=request.user,
        status='borrowed'
    ).order_by('due_date')
    
    # 获取借阅历史
    borrow_history = BookBorrowing.objects.filter(
        borrower=request.user,
        status='returned'
    ).order_by('-return_date')[:5]
    
    # 获取预约记录 - 修正字段名
    reservations = BookReservation.objects.filter(
        reservationer=request.user  
    ).order_by('-reservation_date')[:5]

    context = {
        'user_stats': user_stats,
        'current_borrowings': current_borrowings,
        'borrow_history': borrow_history,
        'reservations': reservations,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    """编辑个人信息"""
    if not request.user.is_authenticated:
        messages.error(request, '请先登录')
        return redirect('login')

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人信息更新成功！')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def notification_list(request):
    """通知列表视图"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def mark_notification_read(request, pk):
    """标记单个通知为已读"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notification_list')

@login_required
def mark_all_notifications_read(request):
    """标记所有通知为已读"""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, '所有通知已标记为已读')
    return redirect('notification_list')

def create_notification(user, notification_type, title, message, related_book=None):
    """创建通知的辅助函数"""
    Notification.objects.create(
        recipient=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_book=related_book
    )

@login_required
@permission_required('books.manage_books', raise_exception=True)
def manage_books(request):
    """图书管理视图"""

@login_required
@permission_required('auth.change_user', raise_exception=True)
def manage_permissions(request):
    """权限管理视图"""
    users = User.objects.all().prefetch_related('groups', 'user_permissions')
    groups = Group.objects.all().prefetch_related('permissions')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        group_id = request.POST.get('group_id')
        action = request.POST.get('action')
        
        if all([user_id, group_id, action]):
            user = User.objects.get(id=user_id)
            group = Group.objects.get(id=group_id)
            
            if action == 'add':
                user.groups.add(group)
                messages.success(request, f'已将用户 {user.username} 添加到 {group.name} 组')
            elif action == 'remove':
                user.groups.remove(group)
                messages.success(request, f'已将用户 {user.username} 从 {group.name} 组移除')
    
    context = {
        'users': users,
        'groups': groups,
    }
    return render(request, 'admin/manage_permissions.html', context)

@login_required
@permission_required('auth.view_user', raise_exception=True)
def admin_notification_list(request):
    """通知管理视图"""
    if not request.user.is_staff:
        messages.error(request, '您没有权限访问此页面')
        return redirect('index')
        
    notifications = Notification.objects.all().order_by('-created_at')
    context = {
        'notifications': notifications,
        'section': 'notifications',
        'title': '通知管理',  # 添加标题
        'site_title': '图书管理系统',  # 添加站点标题
        'site_header': '图书管理系统后台',  # 添加站点头部
    }
    return render(request, 'admin/notification_list.html', context)

@login_required
@permission_required('auth.view_user', raise_exception=True)
def admin_message_list(request):
    """消息管理视图"""
    if not request.user.is_staff:
        messages.error(request, '您没有权限访问此页面')
        return redirect('index')
        
    system_messages = Notification.objects.filter(notification_type='system').order_by('-created_at')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        recipients = request.POST.getlist('recipients')
        
        for user_id in recipients:
            user = User.objects.get(id=user_id)
            create_notification(
                user=user,
                notification_type='system',
                title=title,
                message=message
            )
        messages.success(request, '消息发送成功！')
        return redirect('admin_message_list')
    
    context = {
        'system_messages': system_messages,
        'users': User.objects.all(),
        'section': 'messages',
        'title': '消息管理',  # 添加标题
        'site_title': '图书管理系统',  # 添加站点标题
        'site_header': '图书管理系统后台',  # 添加站点头部
    }
    return render(request, 'admin/message_list.html', context)
