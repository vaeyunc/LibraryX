from django.shortcuts import render, get_list_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from .models import Book, BookBorrowing, Category
from .forms import BookSearchForm, RegisterForm
from django.db.models import Count, F, Q

@login_required
def book_list(request):
    books = Book.objects.all()
    form = BookSearchForm(request.GET) 

    if form.is_valid():
        query = form.cleaned_data.get('query')
        if query:
            books = books.filter(title_icontains=query) | \
                    books.filter(author_icontains=query) | \
                    books.filter(isbn_icontains=query) 
        
        category = form.cleaned_data.get('category')
        if category:
            books = books.filter(category=category)

    return render(request, 'books/book_list.html', {
        'books': books,
        'form': form
    })

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'books/book_detail.html', {'book': book})

@login_required
def borrow_book(request, pk):
    book = get_list_or_404(Book, pk=pk)
    if book.availabe > 0:
        BookBorrowing.objects.create(
            book = book,
            borrower = request.user
        )
        book.availabe -= 1
        book.save()
        messages.success(request, f'您已成功借阅<{book.title}>')
    else:
        messages.error(request, '抱歉，该书已全部借出')
    return redirect('book_detail', pk=pk)
    
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
    
