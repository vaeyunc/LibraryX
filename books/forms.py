from django import forms
from .models import Book, Category, BookBorrowing, BookRecommendation, BookReservation, BookComment, BookReturn
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class BookSearchForm(forms.Form):
    search_query = forms.CharField(
        label = '搜索',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':'输入书名、作者或ISBN'
        })
    )
    category = forms.ModelChoiceField(
        label='类别',
        queryset=Category.objects.all(),
        required=False,
        empty_label="所有类别",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    available_only = forms.BooleanField(
        label='只显示可借',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = '用户名只能包含字母、数字和下划线'
        self.fields['password1'].help_text = '密码至少8位,不能太简单'
        self.fields['password2'].help_text = '请再次输入密码'

class BorrowingForm(forms.ModelForm):
    class Meta:
        model = BookBorrowing
        fields = []



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['email', 'phone', 'avatar']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }