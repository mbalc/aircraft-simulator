"""Unit and Selenium test package for Flights app"""
import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from .models import Plane, Crew, Flight, Airport


class CrewsTest(TestCase):
    """Unit tests for crew assignment code correctness"""

    def setUp(self):
        """Add initial data to db and authenticate future POST requests"""
        now = datetime.now(tz=timezone.utc)
        airport1 = Airport.objects.create(name="a1")
        airport2 = Airport.objects.create(name="a2")
        plane1 = Plane.objects.create(identifier="p1", passengerLimit=20)
        plane2 = Plane.objects.create(identifier="p2", passengerLimit=20)
        # @formatter:off
        flight1 = Flight.objects \
            .create(plane=plane1,
                    takeoffAirport=airport1, takeoffTime=now - timedelta(hours=3, minutes=13),
                    landingAirport=airport2, landingTime=now + timedelta(hours=1),
                   )
        flight2 = Flight.objects \
            .create(plane=plane2,
                    takeoffAirport=airport2, takeoffTime=now - timedelta(hours=3),
                    landingAirport=airport1, landingTime=now + timedelta(hours=1, minutes=25),
                   )
        flight3 = Flight.objects \
            .create(plane=plane2,
                    takeoffAirport=airport1,
                    takeoffTime=now + timedelta(days=1, hours=1, minutes=41),
                    landingAirport=airport2, landingTime=now + timedelta(days=1, hours=5),
                   )
        # @formatter:on
        crew1 = Crew.objects.create(cptName='n1', cptSurname='s1')
        crew2 = Crew.objects.create(cptName='n2', cptSurname='s2')
        crew3 = Crew.objects.create(cptName='n3', cptSurname='s3')

        for elem in [airport1, airport2, plane1, plane2, flight1, flight2, flight3,
                     crew1, crew2, crew3]:
            elem.save()

        # all requests made are authenticated
        user = User.objects.create(username='asdf', password='qwer')
        self.client.force_login(user)

    def bind_crew(self, crew_index, flight_index):
        """Send request to REST api that will attempt binding a crew to a flight"""
        return self.client.post('/REST/setCrew', data=json.dumps({
            'crew': Crew.objects.all()[crew_index].pk,
            'flight': Flight.objects.all()[flight_index].pk,
        }), content_type='json/application', follow=True)

    def check_binding_response(self, crew_index, flight_index, should_succeed, expected_crew):
        """Make a request and check if its results are relevant to what we expected"""
        response = self.bind_crew(crew_index, flight_index)
        if should_succeed:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 400)

        if isinstance(expected_crew, int):
            expected_crew = Crew.objects.all()[expected_crew]
        self.assertEqual(Flight.objects.all()[flight_index].crew, expected_crew)

    def test_captain_name_surname(self):
        """Don't allow two crews to have captains of same name"""
        crew = Crew.objects.all()[0]
        self.assertRaises(IntegrityError, Crew.objects.create,
                          cptName=crew.cptName, cptSurname=crew.cptSurname)

    def test_crew_two_flights_same_time(self):
        """Don't allow a crew to fly two flights at the same time"""
        self.check_binding_response(2, 0, True, 2)  # 2 . .
        self.check_binding_response(2, 1, False, None)  # flights 0 and 1 at same time
        self.check_binding_response(0, 2, True, 0)  # 2 . 0
        self.check_binding_response(1, 1, True, 1)  # 2 1 0
        self.check_binding_response(2, 1, False, 1)
        self.check_binding_response(1, 0, False, 2)

    def test_crew_reassignment(self):
        """Check if reassigning flight crews works as expected"""
        self.check_binding_response(0, 0, True, 0)  # 0 . .
        self.check_binding_response(1, 2, True, 1)  # 0 . 1
        self.check_binding_response(1, 1, True, 1)  # 0 1 1
        self.check_binding_response(0, 2, True, 0)  # 0 1 0
        self.check_binding_response(2, 0, True, 2)  # 2 1 0
        self.check_binding_response(0, 1, True, 0)  # 2 0 0
