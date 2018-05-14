from random import randint, randrange
from datetime import datetime as dt, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from flights.models import Airport, Flight, Passenger, Reservation, Plane

AIRPORTS = ['Moscow', 'Paris', 'Berlin', 'London', 'Warsaw', 'Stockholm', 'Kopenhagen', 'Madrid',
            'New York', 'Lviv', 'Budapest', 'Athens', 'Cairo', 'Tokyo', 'Praha', 'Sydney', 'Oslo']

PLANE_COUNT = 50
FLIGHTS_PER_PLANE = 50
FLIGHT_LENGTH_MINUTE_RANGE = 30, 720
FLIGHT_SPAN_MINUTE_RANGE = 30, 1440


def rand_char():
    return chr(ord('A') + randrange(ord('z') - ord('a')))


def rand_id():
    return str(randrange(9))


def str_rep(i: int, funct):
    if i <= 0:
        return ''
    return funct() + str_rep(i - 1, funct)


def main():
    # cleanup all models
    for model in [Reservation, Flight, Passenger, Plane, Airport]:
        model.objects.all().delete()

    # init airports
    for airport_name in AIRPORTS:
        Airport.objects.create(name=airport_name)

    airport_objs = Airport.objects.all()

    # init planes
    for i in range(PLANE_COUNT):
        print('Plane', i)
        identifier = str_rep(2, rand_char) + str_rep(3, rand_id)
        passenger_limit = randint(20, 120)
        plane = Plane(identifier=identifier, passengerLimit=passenger_limit)
        plane.save()
        landing_time = dt.now(tz=timezone.utc)

        # init flights for each plane
        while Flight.objects.filter(plane=plane).count() < FLIGHTS_PER_PLANE:
            takeoff_airport_id = randrange(airport_objs.count())
            landing_airport_id = randrange(airport_objs.count() - 1)
            if landing_airport_id >= takeoff_airport_id:
                landing_airport_id += 1

            takeoff_time = landing_time + timedelta(minutes=randrange(*FLIGHT_SPAN_MINUTE_RANGE))
            landing_time = takeoff_time + timedelta(minutes=randrange(*FLIGHT_LENGTH_MINUTE_RANGE))

            try:
                with transaction.atomic():
                    Flight.objects.create(takeoffAirport=airport_objs[takeoff_airport_id],
                                          landingAirport=airport_objs[landing_airport_id],
                                          takeoffTime=takeoff_time, landingTime=landing_time,
                                          plane=plane)
            except ValidationError:
                print('Avoiding plane overuse by cancelling a generated flight')


main()
