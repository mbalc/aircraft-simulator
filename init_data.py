from flights.models import Airport, Flight, Passenger, Reservation, Plane
from random import randint, randrange
from datetime import datetime as dt, timedelta
from django.utils import timezone

AIRPORTS = ['Moscow', 'Paris', 'Berlin', 'London', 'Warsaw', 'Stockholm', 'Kopenhagen', 'Madrid',
            'New York', 'Lviv', 'Budapest', 'Athens', 'Cairo', 'Tokyo', 'Praha', 'Sydney', 'Oslo']

PLANE_COUNT = 50
FLIGHTS_PER_PLANE = 50
FLIGHT_LENGTH_MINUTE_RANGE = 40, 720
FLIGHT_SPAN_MINUTE_RANGE = 30, 1440


def rand_char():
    return chr(ord('A') + randrange(ord('z') - ord('a')))


def rand_id():
    return str(randrange(9))


def str_rep(i: int, f):
    if i <= 0:
        return ''
    return f() + str_rep(i - 1, f)


def main():
    # cleanup all models
    for model in [Reservation, Flight, Passenger, Plane, Airport]:
        model.objects.all().delete()

    # init airports
    for a in AIRPORTS:
        Airport.objects.create(name=a)

    airportObjs = Airport.objects.all()

    # init planes
    for _ in range(PLANE_COUNT):
        identifier = str_rep(2, rand_char) + str_rep(3, rand_id)
        passengerLimit = randint(20, 120)
        plane = Plane(identifier=identifier, passengerLimit=passengerLimit)
        plane.save()
        landingTime = dt.now(tz=timezone.utc)

        # init flights for each plane
        while Flight.objects.filter(plane=plane).count() < FLIGHTS_PER_PLANE:
            takeoffAirportId = randrange(airportObjs.count())
            landingAirportId = randrange(airportObjs.count() - 1)
            if landingAirportId >= takeoffAirportId:
                landingAirportId += 1

            takeoffTime = landingTime + timedelta(minutes=randrange(*FLIGHT_SPAN_MINUTE_RANGE))
            landingTime = takeoffTime + timedelta(minutes=randrange(*FLIGHT_LENGTH_MINUTE_RANGE))

            Flight.objects.create(takeoffAirport=airportObjs[takeoffAirportId],
                                  landingAirport=airportObjs[landingAirportId],
                                  takeoffTime=takeoffTime, landingTime=landingTime, plane=plane)


main()
