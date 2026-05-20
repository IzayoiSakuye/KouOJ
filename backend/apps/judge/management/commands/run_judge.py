import time

from django.core.management.base import BaseCommand

from apps.judge.services import process_next_submission


class Command(BaseCommand):
    help = "Run the simple KouOJ judge worker."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Only process one pending submission.")
        parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds when queue is empty.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Judge worker started."))
        while True:
            submission = process_next_submission()
            if submission:
                self.stdout.write(f"Judged submission #{submission.id}: {submission.status}")
            elif options["once"]:
                self.stdout.write("No pending submission.")
                return
            else:
                time.sleep(options["sleep"])

            if options["once"]:
                return
