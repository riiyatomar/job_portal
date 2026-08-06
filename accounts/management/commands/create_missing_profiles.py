from django.core.management.base import BaseCommand
from accounts.models import CustomUser, Profile

class Command(BaseCommand):
    help = 'Creates missing profiles for existing users'

    def handle(self, *args, **kwargs):
        users_without_profile = CustomUser.objects.filter(profile__isnull=True)
        count = users_without_profile.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('All users already have a profile.'))
            return
            
        created_count = 0
        for user in users_without_profile:
            Profile.objects.get_or_create(user=user)
            created_count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} missing profiles.'))
