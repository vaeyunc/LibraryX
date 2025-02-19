from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('book/<int:pk>/return/', views.return_book, name='return_book'),
    path('my-borrowings/', views.my_borrowings, name='my_borrowings'),
    path('library-status/', views.library_status, name='library_status'),
]