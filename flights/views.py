"""Provide data for templates"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, SuspiciousOperation
from django.db import transaction
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_GET

import json

from flights.models import Flight, Reservation, Passenger, Crew


class DbIntegrityError(ValidationError, SuspiciousOperation):
    """Raise both types of message both for db to revert commit and view dispatcher
    to trigger a 400 status page"""
    x = 3  # don't need to do anything


# Create your views here.


def flights(request):
    """Show all flights, optionally filtered by day"""
    date_query = request.GET.get('search')
    flight_list = Flight.objects.select_for_update().order_by('takeoffTime', 'landingTime')
    if date_query:
        flight_list = flight_list.filter(takeoffTime__date__lte=date_query,
                                         landingTime__date__gte=date_query)

    return render(request, 'flights.html', {'flight_list': flight_list})


def details(request, **kwargs):
    """Show details of a flight, allow for reserving seats by authorized passengers"""
    flight = get_object_or_404(Flight, pk=kwargs.get('pkey'))
    reservations = Reservation.objects.select_for_update() \
        .filter(flight=flight, ticketCount__gt=0).order_by('-updated')
    ticks = reservations.aggregate(total=Coalesce(Sum('ticketCount'), Value(0)))
    free_seats = flight.plane.passengerLimit - ticks.get('total')

    return render(request, 'details.html', {'flight': flight, 'reservations': reservations,
                                            'ticks': ticks, 'free_seats': free_seats})


@transaction.atomic
@require_POST
@login_required
def reserve(request):
    """Attempt a new reservation of tickets by an authorized passenger"""
    try:
        passenger, _ = Passenger.objects.select_for_update() \
            .get_or_create(name=request.POST['name'], surname=request.POST['surname'])
        flight = Flight.objects.select_for_update().get(pk=request.POST['flight'])
        reservation, _ = Reservation.objects.select_for_update() \
            .get_or_create(passenger=passenger, flight=flight)
        reservation.ticketCount = request.POST['ticketCount']
        reservation.save()
    except (SuspiciousOperation, ValidationError) as err:
        raise DbIntegrityError(err)

    return redirect('details', request.POST['flight'])


def my_error_handler(request, exception, template_name='400.html'):
    """Show a 400 page with details of a cause if provided"""
    # response = render_to_response('400.html', context_instance=RequestContext(request))
    # response.status_code = 400
    # return response
    return HttpResponseBadRequest(render(request, template_name, {'details': str(exception)}))


def make_json_detailed_model_list(model_list):
    """Create a list of model details that is extended by a result of __str__ call on a model obj"""
    return dict((obj.id, dict(model_to_dict(obj), **{'title': obj.__str__()}))
                for obj in model_list)


@require_GET
def get_flights(request):
    """Return a JSON of all flights, optionally filtered by date"""
    date_query = request.GET.get('search')
    flight_list = Flight.objects.select_for_update().order_by('takeoffTime', 'landingTime')
    if date_query:
        flight_list = flight_list.filter(takeoffTime__date__lte=date_query,
                                         landingTime__date__gte=date_query)

    out = make_json_detailed_model_list(flight_list)
    return JsonResponse({'response': out}, status=200)


@require_GET
# pylint: disable=unused-argument
# Needed for a view to be valid
def get_crews(request):
    # pylint: enable=unused-argument
    """Return a JSON of all crews"""
    crew_list = Crew.objects.select_for_update()
    out = make_json_detailed_model_list(crew_list)
    return JsonResponse({'response': out}, status=200)


@transaction.atomic
@require_POST
@login_required
def set_crew(request):
    """Bind a crew to lead a flight"""
    body = json.loads(request.body)
    print(body)
    try:
        crew = Crew.objects.select_for_update().get(pk=body['crew'])
        flight = Flight.objects.select_for_update().get(pk=body['flight'])
        flight.crew = crew
        flight.save()
    except (SuspiciousOperation, ValidationError) as err:
        return HttpResponseBadRequest(str(err))

    return HttpResponse('OK')
