from django.core.management.base import BaseCommand
from django.utils import timezone
from books.models import BookBorrowing
from books.views import create_notification

class Command(BaseCommand):
    help = '检查逾期图书并发送提醒'

    def handle(self, *args, **options):
        # 查找即将到期的图书（3天内）
        soon_due = BookBorrowing.objects.filter(
            status='borrowed',
            due_date__range=[timezone.now(), timezone.now() + timezone.timedelta(days=3)]
        )
        
        for borrowing in soon_due:
            create_notification(
                user=borrowing.borrower,
                notification_type='overdue',
                title=f'图书即将到期提醒',
                message=f'您借阅的《{borrowing.book.title}》将在 {borrowing.due_date.strftime("%Y-%m-%d")} 到期，请及时归还。',
                related_book=borrowing.book
            )
            
        # 查找已逾期的图书
        overdue = BookBorrowing.objects.filter(
            status='borrowed',
            due_date__lt=timezone.now()
        )
        
        for borrowing in overdue:
            create_notification(
                user=borrowing.borrower,
                notification_type='overdue',
                title=f'图书逾期提醒',
                message=f'您借阅的《{borrowing.book.title}》已逾期，请尽快归还。',
                related_book=borrowing.book
            ) 