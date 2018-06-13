"""Unit and Selenium test package for Flights app"""
import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from selenium import webdriver

from .models import Plane, Crew, Flight, Airport, Reservation, Passenger


def init_database():
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


class UITest(StaticLiveServerTestCase):
    """Test behaviour of frontend and effects of its usage on backend"""

    def getUser(self):
        return self.creds['user']

    def getPass(self):
        return self.creds['pass']

    def login(self):
        driver = self.driver

        driver.find_element_by_name("username").send_keys(self.getUser())
        driver.find_element_by_name("password").send_keys(self.getPass())

        driver.find_element_by_xpath("//button[@type='submit']").click()

    def visit_home(self):
        return self.driver.get('%s%s' % (self.live_server_url, '/'))

    def setUp(self):
        """Add initial data to db and authenticate future POST requests"""
        self.driver = webdriver.Firefox()

        init_database()

        self.creds = {'user': 'asdf', 'pass': 'qwer'}
        User.objects.create_user(username=self.getUser(), password=self.getPass())

        self.visit_home()
        self.login()

    def reserve(self, inputs):
        driver = self.driver
        for field, data in zip(["name", "surname", "ticketCount"], inputs):
            driver.find_element_by_id(field).clear()
            driver.find_element_by_id(field).send_keys(data)
        driver.find_element_by_xpath("//button[@type='submit']").click()

    def check_tickets(self, row, data):
        driver = self.driver
        equals = self.assertEqual
        for col in range(len(data)):
            equals(data[col], driver.find_element_by_xpath(
                '//details[2]/table/tbody/tr[%s]/td[%s]' % (row, str(col + 1))).text)

        passengers = Passenger.objects.filter(name=data[0], surname=data[1])
        self.assertEquals(1, len(passengers))
        self.assertTrue(Reservation.objects.filter(passenger=passengers[0],
                                                   ticketCount=int(data[2])))

    def test_add_passenger(self):
        driver = self.driver
        reservations = [
            ["Jan", "Kowalski", "8"],
            ["Ewa", "Nowak", "9"],
            ["Tadeusz", "Kościuszko", "10"],
        ]

        driver.find_element_by_xpath("//tr[2]/td[2]").click()  # access flight detail page
        self.assertEqual("No reservations made for this flight",
                         driver.find_element_by_xpath("//details[2]/table/tbody/tr/td").text)
        self.assertEqual(0, Passenger.objects.count())

        self.reserve(reservations[0])
        self.check_tickets("1", reservations[0])

        driver.execute_script("window.open()")  # new tab
        driver.switch_to.window(self.driver.window_handles[1])
        self.visit_home()
        driver.find_element_by_xpath("//tr[2]/td[2]").click()
        self.check_tickets("1", reservations[0])

        self.reserve(reservations[1])
        self.check_tickets("1", reservations[1])
        self.check_tickets("2", reservations[0])

        driver.switch_to.window(self.driver.window_handles[0])
        self.check_tickets("1", reservations[0])

        self.reserve(reservations[2])  # attempt to try to reserve too many tickets
        self.assertEqual("Your request is not right somehow",
                         driver.find_element_by_xpath("//h1").text)

class CrewsTest(TestCase):
    """Unit tests for crew assignment code correctness"""

    def setUp(self):
        """Add initial data to db and authenticate future POST requests"""
        init_database()

        # all requests made will be authenticated
        user = User.objects.create(username='asdf', password='qwer')
        user.save()
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
