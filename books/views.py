from django.shortcuts import render, get_list_or_404, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Book, BookBorrowing, Category, BookReturn, BookReservation, UserProfile
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
def borrow_book(request, pk):
    """借书视图"""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BorrowingForm(request.POST)
        if form.is_valid() and book.available > 0:
            borrowing = form.save(commit=False)
            borrowing.book = book
            borrowing.borrower = request.user
            borrowing.save()
            
            book.available -= 1
            book.save()
            
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
def return_book(request, pk):
    borrowing = get_object_or_404(
        BookBorrowing,
        book_id = pk,
        borrower = request.user,
        returned= False
    )
    borrowing.returned = True
    borrowing.return_date = timezone.now()
    borrowing.save()

    book = borrowing.book
    book.available += 1
    book.save()

    messages.success(request, f'您已成功归还<{book.title}>')
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
        reservationer=request.user  # 修改这里：使用正确的字段名 reservationer
    ).order_by('-reservation_date')  # 修改这里：使用正确的字段名 reservation_date

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
