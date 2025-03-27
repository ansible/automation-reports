from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Change password for existing user"

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError('ERROR changing password, user {} does not exist'.format(username))
        if user.check_password(password):
            self.stdout.write('Password unmodified for user {}.'.format(username))
            return

        user.set_password(password)
        self.stdout.write(self.style.NOTICE('Password updated for user {}.'.format(username)))
        user.save()
