import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from .models import Plane, Crew, Flight, Airport


class CrewsTest(TestCase):
    def setUp(self):
        now = datetime.now(tz=timezone.utc)
        a1 = Airport.objects.create(name="a1")
        a2 = Airport.objects.create(name="a2")
        p1 = Plane.objects.create(identifier="p1", passengerLimit=20)
        p2 = Plane.objects.create(identifier="p2", passengerLimit=20)
        f1 = Flight.objects \
            .create(plane=p1,
                    takeoffAirport=a1, takeoffTime=now - timedelta(hours=3, minutes=13),
                    landingAirport=a2, landingTime=now + timedelta(hours=1),
                    )
        f2 = Flight.objects \
            .create(plane=p2,
                    takeoffAirport=a2, takeoffTime=now - timedelta(hours=3),
                    landingAirport=a1, landingTime=now + timedelta(hours=1, minutes=25),
                    )
        f3 = Flight.objects \
            .create(plane=p2,
                    takeoffAirport=a1, takeoffTime=now + timedelta(days=1, hours=1, minutes=41),
                    landingAirport=a2, landingTime=now + timedelta(days=1, hours=5),
                    )
        c1 = Crew.objects.create(cptName='n1', cptSurname='s1')
        c2 = Crew.objects.create(cptName='n2', cptSurname='s2')

        for elem in [a1, a2, p1, p2, f1, f2, f3, c1, c2]:
            elem.save()

        # all requests made are authenticated
        u = User.objects.create(username='asdf', password='qwer')
        self.client.force_login(u)

    def bind_crew(self, crew, flight):
        return self.client.post('/REST/setCrew', data=json.dumps({
            'crew': crew.pk,
            'flight': flight.pk,
        }), content_type='json/application', follow=True)

    def test_captain_name_surname(self):
        c = Crew.objects.all()[0]
        self.assertRaises(IntegrityError, Crew.objects.create,
                          cptName=c.cptName, cptSurname=c.cptSurname)

    def test_crew_two_flights_same_time(self):
        [c1] = Crew.objects.all()[0:1]
        [f1, f2] = Flight.objects.all()[0:2]

        response = self.bind_crew(c1, f1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Flight.objects.all()[0].crew, c1)  # f1.crew now equals c1

        response = self.bind_crew(c1, f2)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(f2.crew, None)
