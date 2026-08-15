"""
Populate the database with demonstration data for CutZone.

Usage:
    python manage.py seed_demo

Creates:
    * 3 services (Haircut, Haircut + Beard, Full Package)
    * 4 barbers (Victor, Jacob, Emmanuel, John) with weekly schedules
    * an admin account       -> username: admin  / password: admin12345
    * a demo customer        -> username: demo   / password: demo12345
    * a few example appointments and approved reviews

The command is idempotent: running it twice will not duplicate data.
"""

import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from barbers.models import Barber, BarberSchedule
from bookings.models import Appointment
from reviews.models import Review
from services.models import Service


class Command(BaseCommand):
    help = "Seed the database with CutZone demonstration data."

    def handle(self, *args, **options):
        self.stdout.write("Seeding CutZone demo data…")

        # ------------------------------------------------------------- #
        # Services
        # ------------------------------------------------------------- #
        services_data = [
            {
                "name": "Haircut",
                "price": 3000,
                "duration_minutes": 30,
                "description": (
                    "A precise classic or modern haircut finished with clean "
                    "line-ups and styling."
                ),
            },
            {
                "name": "Haircut + Beard",
                "price": 4500,
                "duration_minutes": 45,
                "description": (
                    "A full haircut plus expert beard shaping, trimming and a "
                    "hot-towel finish."
                ),
            },
            {
                "name": "Full Package",
                "price": 6000,
                "duration_minutes": 60,
                "description": (
                    "The complete CutZone experience: haircut, beard sculpting, "
                    "facial cleanse and premium styling."
                ),
            },
        ]
        services = {}
        for data in services_data:
            svc, created = Service.objects.get_or_create(
                name=data["name"], defaults=data
            )
            services[svc.name] = svc
            self._log("Service", svc.name, created)

        # ------------------------------------------------------------- #
        # Barbers + schedules (Mon–Sat 8:00–19:00, Sunday off)
        # ------------------------------------------------------------- #
        barbers_data = [
            {
                "name": "Victor",
                "specialization": "Fades & Modern Styles",
                "bio": (
                    "Victor has over 8 years of experience delivering razor-sharp "
                    "fades and contemporary cuts. Known for his attention to detail."
                ),
            },
            {
                "name": "Jacob",
                "specialization": "Beard Sculpting & Hot Towel Shaves",
                "bio": (
                    "Jacob is CutZone's beard specialist. From full beard designs "
                    "to classic hot-towel shaves, he keeps every beard sharp."
                ),
            },
            {
                "name": "Emmanuel",
                "specialization": "Classic Cuts & Kids' Styles",
                "bio": (
                    "Emmanuel blends timeless barbering with a friendly touch, "
                    "making him a favourite for gentlemen and kids alike."
                ),
            },
            {
                "name": "John",
                "specialization": "Creative Designs & Hair Art",
                "bio": (
                    "John turns haircuts into artwork. Patterns, waves and "
                    "freestyle designs are his signature at CutZone."
                ),
            },
        ]
        barbers = {}
        for data in barbers_data:
            barber, created = Barber.objects.get_or_create(
                name=data["name"], defaults=data
            )
            barbers[barber.name] = barber
            self._log("Barber", barber.name, created)
            # Attach the bundled demo photo if present in media/barbers/.
            photo_rel = f"barbers/{barber.name.lower()}.jpg"
            from django.conf import settings as dj_settings
            if not barber.photo and (dj_settings.MEDIA_ROOT / photo_rel).exists():
                barber.photo = photo_rel
                barber.save()
            for weekday in range(7):
                BarberSchedule.objects.get_or_create(
                    barber=barber,
                    weekday=weekday,
                    defaults={
                        "is_working": weekday != 6,  # Sunday off
                        "start_time": datetime.time(8, 0),
                        "end_time": datetime.time(19, 0),
                    },
                )

        # ------------------------------------------------------------- #
        # Users
        # ------------------------------------------------------------- #
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@cutzone.ng",
                "first_name": "CutZone",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin12345")
            admin.save()
        self._log("Admin user", "admin (password: admin12345)", created)

        demo, created = User.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@example.com",
                "first_name": "Chinedu",
                "last_name": "Okafor",
            },
        )
        if created:
            demo.set_password("demo12345")
            demo.save()
            demo.profile.phone = "+234 803 555 0101"
            demo.profile.address = "12 Wetheral Road, Owerri"
            demo.profile.save()
        self._log("Demo customer", "demo (password: demo12345)", created)

        # ------------------------------------------------------------- #
        # Example appointments (only if the demo user has none yet)
        # ------------------------------------------------------------- #
        if not Appointment.objects.filter(customer=demo).exists():
            today = datetime.date.today()

            def make(days, time, barber, service, status):
                start = datetime.time(*time)
                end_dt = datetime.datetime.combine(
                    today, start
                ) + datetime.timedelta(minutes=service.duration_minutes)
                return Appointment.objects.create(
                    customer=demo,
                    barber=barber,
                    service=service,
                    date=today + datetime.timedelta(days=days),
                    start_time=start,
                    end_time=end_dt.time(),
                    price=service.price,
                    status=status,
                )

            # Two completed past appointments (for history + reviews).
            a1 = make(-14, (10, 0), barbers["Victor"], services["Haircut"],
                      Appointment.STATUS_COMPLETED)
            a2 = make(-7, (15, 30), barbers["Jacob"], services["Haircut + Beard"],
                      Appointment.STATUS_COMPLETED)
            # One cancelled appointment.
            make(-3, (12, 0), barbers["John"], services["Haircut"],
                 Appointment.STATUS_CANCELLED)
            # Upcoming appointments.
            make(2, (11, 0), barbers["Emmanuel"], services["Full Package"],
                 Appointment.STATUS_CONFIRMED)
            make(5, (9, 30), barbers["Victor"], services["Haircut"],
                 Appointment.STATUS_PENDING)

            # Reviews for the completed appointments.
            Review.objects.create(
                appointment=a1, customer=demo, rating=5,
                comment=(
                    "Victor gave me the cleanest fade I've had in years. "
                    "The shop feels premium and the service was quick."
                ),
            )
            Review.objects.create(
                appointment=a2, customer=demo, rating=4,
                comment=(
                    "Jacob really knows beards. Great hot towel finish — "
                    "will definitely be coming back."
                ),
            )
            self.stdout.write(self.style.SUCCESS("  ✓ Example appointments & reviews created"))
        else:
            self.stdout.write("  • Example appointments already exist — skipped")

        self.stdout.write(self.style.SUCCESS("Done! Demo data is ready."))
        self.stdout.write("")
        self.stdout.write("Log in with:")
        self.stdout.write("  Admin   → username: admin  password: admin12345")
        self.stdout.write("  Customer→ username: demo   password: demo12345")

    def _log(self, kind, name, created):
        mark = "✓ created" if created else "• exists"
        self.stdout.write(f"  {mark}: {kind} — {name}")
