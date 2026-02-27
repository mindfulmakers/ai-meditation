from django.core.management import BaseCommand

from teams.models import Team


class Command(BaseCommand):
    help = "Debugging command"

    def handle(self, *args, **options):
        Team.objects.all().first().link_team_user()
