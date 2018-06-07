from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, SuspiciousOperation
from django.db import transaction
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_GET

from flights.models import Flight, Reservation, Passenger


class DbIntegrityError(ValidationError, SuspiciousOperation):
    ...

# Create your views here.


def flights(request):
    date_query = request.GET.get('search')
    flight_list = Flight.objects.select_for_update().order_by('takeoffTime', 'landingTime')
    if date_query:
        flight_list = flight_list.filter(takeoffTime__date__lte=date_query,
                                         landingTime__date__gte=date_query)

    return render(request, 'flights.html', locals())


def details(request, **kwargs):
    flight = get_object_or_404(Flight, pk=kwargs.get('pkey'))
    reservations = Reservation.objects.select_for_update() \
        .filter(flight=flight, ticketCount__gt=0).order_by('-updated')
    ticks = reservations.aggregate(total=Coalesce(Sum('ticketCount'), Value(0)))
    free_seats = flight.plane.passengerLimit - ticks.get('total')

    return render(request, 'details.html', locals())


@transaction.atomic
@require_POST
@login_required
def reserve(request):
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
    print('page not found start!')
    # response = render_to_response('400.html', context_instance=RequestContext(request))
    # response.status_code = 400
    # return response
    return HttpResponseBadRequest(render(request, template_name, {'details': str(exception)}))


@require_GET
def get_flights(request):
    out = list(Flight.objects.select_for_update().values())
    return JsonResponse({'request': request, 'response': out}, status=200)
