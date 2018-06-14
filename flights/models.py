"""Define data entities used by the whole flight management app"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import Value, Q
from django.db.models.functions import Coalesce
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models

DAILY_FLIGHTS_PER_PLANE = 4
MIN_SEAT_COUNT = 20
MIN_FLIGHT_MINUTES = 30


#
@receiver(post_save)
# pylint: disable=unused-argument
# This format of function arguments is needed by Django
def post_save_handler(sender, instance, *args, **kwargs):
    # pylint: enable=unused-argument
    """Ensure after a change made to the db state that everything is all right; throw an exception
    that will cause a rollback of an atomic transaction in case of database integrity violation
    during the ongoing model instance update/creation"""
    instance.full_clean()


class Airport(models.Model):
    """Points of flight's start or end"""
    name = models.TextField(unique=True)

    def __str__(self):
        return 'Airport in %s' % self.name


class Plane(models.Model):
    """Vehicle that a flight is made with, has a limited seat space"""
    identifier = models.TextField(unique=True, primary_key=True)
    passengerLimit = models.PositiveIntegerField(validators=[MinValueValidator(MIN_SEAT_COUNT)])

    def __str__(self):
        return 'Plane %s with %d seats' % (self.identifier, self.passengerLimit)


class Crew(models.Model):
    """A team identified by it's captain's credentials that can be assigned to guide a flight"""
    cptName = models.TextField()
    cptSurname = models.TextField()

    class Meta:
        unique_together = ('cptName', 'cptSurname')

    def __str__(self):
        return '%s %s\'s crew' % (self.cptName, self.cptSurname)


class Passenger(models.Model):
    """Entity that can reserve tickets for a flight, taking up a plane seats"""
    name = models.TextField()
    surname = models.TextField()

    class Meta:
        unique_together = ('name', 'surname')

    def __str__(self):
        return 'Passenger %s %s' % (self.name, self.surname)


class Reservation(models.Model):
    """Tells about how many seats has a passenger reserved"""
    passenger = models.ForeignKey('Passenger', on_delete=models.CASCADE)
    flight = models.ForeignKey('Flight', on_delete=models.CASCADE)

    ticketCount = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('passenger', 'flight')

    def __str__(self):
        return 'Reservation of %d seats by %s for %s' % (self.ticketCount, self.passenger,
                                                         self.flight)

    def clean(self):
        """Check if we did exceed plane's seat limit"""
        total_tickets = Reservation.objects \
            .filter(flight=self.flight) \
            .aggregate(total=Coalesce(models.Sum('ticketCount'), Value(0)))['total']
        if self.flight.plane.passengerLimit < total_tickets:
            raise ValidationError('Such reservation would exceed plane passenger capacity limit')
        return super().clean()


def during(date, plane):
    """How many flights are done on a given day with a given airplane"""
    return Flight.objects \
        .filter(plane=plane) \
        .exclude(landingTime__date__lt=date) \
        .exclude(takeoffTime__date__gt=date).count()


class Flight(models.Model):
    """The main entity of out interest"""
    takeoffAirport = models.ForeignKey('Airport', on_delete=models.CASCADE, related_name='takeoff')
    takeoffTime = models.DateTimeField()

    landingAirport = models.ForeignKey('Airport', on_delete=models.CASCADE, related_name='landing')
    landingTime = models.DateTimeField()

    plane = models.ForeignKey('Plane', on_delete=models.CASCADE)
    crew = models.ForeignKey('Crew', on_delete=models.CASCADE, null=True, blank=True, default=None)

    def __str__(self):
        led_suffix = ''
        if self.crew and self.crew is not None:
            led_suffix = ' led by %s' % self.crew
        return 'Flight of %s from %s to %s (%s - %s)%s' % (
            self.plane, self.takeoffAirport, self.landingAirport,
            self.takeoffTime.__format__("%d %B %Y, %H:%M"),
            self.landingTime.__format__("%d %B %Y, %H:%M"), led_suffix
        )

    def clean(self):
        """Check if all corner cases are met"""
        if self.takeoffAirport == self.landingAirport:
            raise ValidationError('Zero-length flight')
        if self.landingTime <= self.takeoffTime:
            raise ValidationError('Takeoff and landing times are invalid')
        if self.landingTime - self.takeoffTime < timedelta(minutes=MIN_FLIGHT_MINUTES):
            raise ValidationError('Flight time is too short')
        if during(self.takeoffTime.date(), self.plane) > DAILY_FLIGHTS_PER_PLANE or during(
                self.landingTime.date(), self.plane) > DAILY_FLIGHTS_PER_PLANE:
            raise ValidationError('Plane flight limit per day would be exceeded')

        simultaneous_flights = Flight.objects.filter(
            Q(takeoffTime__range=(self.takeoffTime, self.landingTime)) |
            Q(landingTime__range=(self.takeoffTime, self.landingTime)) |
            (Q(takeoffTime__lte=self.takeoffTime) & Q(landingTime__gte=self.landingTime)))

        if self.crew and simultaneous_flights.filter(crew=self.crew).filter(~Q(pk=self.pk))\
                .exists():
            raise ValidationError('One crew would have to supervise two flights at the same time')
        if simultaneous_flights.filter(plane=self.plane).filter(~Q(pk=self.pk)).exists():
            raise ValidationError('There would be two simultaneous flights of a single plane')

        return super().clean()
