from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models

DAILY_FLIGHTS_PER_PLANE = 4
MIN_SEAT_COUNT = 20


@receiver(post_save)
def post_save_handler(sender, instance, *args, **kwargs):
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

    class Meta:
        unique_together = ('passenger', 'flight')

    def __str__(self):
        return 'Reservation of %d seats by %s for %s' % (self.ticketCount, self.passenger,
                                                         self.flight)

    def clean(self):
        f = self.flight
        g = Reservation.objects.all()[0].flight
        total = Reservation.objects.filter(flight=self.flight).aggregate(total=Coalesce(models.Sum(
                'ticketCount'), Value(0)))
        print('tlt', total)
        if self.flight.plane.passengerLimit < total['total']:
            raise ValidationError('Plane passenger capacity exceeded')


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
