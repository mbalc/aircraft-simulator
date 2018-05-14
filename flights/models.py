from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models

DAILY_FLIGHTS_PER_PLANE = 4
MIN_SEAT_COUNT = 20
MIN_FLIGHT_MINUTES = 30


# Throw an exception that will cause a rollback of an atomic transaction in case of database
# integrity violation during model instance update/creation
@receiver(post_save)
def post_save_handler(_, instance, *args, **kwargs):
    instance.full_clean()


class Airport(models.Model):
    name = models.TextField(unique=True)

    def __str__(self):
        return 'Airport in %s' % self.name


class Plane(models.Model):
    identifier = models.TextField(unique=True, primary_key=True)
    passengerLimit = models.PositiveIntegerField(validators=[MinValueValidator(MIN_SEAT_COUNT)])

    def __str__(self):
        return 'Plane %s with %d seats' % (self.identifier, self.passengerLimit)


class Passenger(models.Model):
    name = models.TextField()
    surname = models.TextField()

    class Meta:
        unique_together = ('name', 'surname')

    def __str__(self):
        return 'Passenger %s %s' % (self.name, self.surname)


class Reservation(models.Model):
    passenger = models.ForeignKey('Passenger', on_delete=models.CASCADE)
    flight = models.ForeignKey('Flight', on_delete=models.CASCADE)

    ticketCount = models.PositiveIntegerField(default=0)

    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('passenger', 'flight')

    def __str__(self):
        return 'Reservation of %d seats by %s for %s' % (self.ticketCount, self.passenger,
                                                         self.flight)

    def clean(self):
        total_tickets = Reservation.objects \
            .filter(flight=self.flight) \
            .aggregate(total=Coalesce(models.Sum('ticketCount'), Value(0)))['total']
        if self.flight.plane.passengerLimit < total_tickets:
            raise ValidationError('Plane passenger capacity exceeded')
        return super().clean()


# How many flights are done on a given day with a given airplane
def during(date, plane):
    return Flight.objects \
        .filter(plane=plane) \
        .exclude(landingTime__date__lt=date) \
        .exclude(takeoffTime__date__gt=date).count()


class Flight(models.Model):
    takeoffAirport = models.ForeignKey('Airport', on_delete=models.CASCADE, related_name='takeoff')
    takeoffTime = models.DateTimeField()

    landingAirport = models.ForeignKey('Airport', on_delete=models.CASCADE, related_name='landing')
    landingTime = models.DateTimeField()

    plane = models.ForeignKey('Plane', on_delete=models.CASCADE)

    def __str__(self):
        return 'Flight of %s from %s to %s (%s - %s)' % (
            self.plane, self.takeoffAirport, self.landingAirport, self.takeoffTime, self.landingTime
        )

    def clean(self):
        if self.takeoffAirport == self.landingAirport:
            raise ValidationError('Zero-length flight')
        if self.landingTime <= self.takeoffTime:
            raise ValidationError('Takeoff and landing times invalid')
        if self.landingTime - self.takeoffTime < timedelta(minutes=MIN_FLIGHT_MINUTES):
            raise ValidationError('Flight time too short')
        if during(self.takeoffTime.date(), self.plane) > DAILY_FLIGHTS_PER_PLANE or during(
                self.landingTime.date(), self.plane) > DAILY_FLIGHTS_PER_PLANE:
            raise ValidationError('Plane flight limit per day exceeded')
        for fli in Flight.objects.filter(plane=self.plane).exclude(pk=self.pk):
            if fli.takeoffTime < self.takeoffTime <= fli.landingTime or fli.takeoffTime <= \
                    self.landingTime <= fli.landingTime:
                raise ValidationError('Two flights of one plane at the same time')

        return super().clean()
