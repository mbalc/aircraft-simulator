from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from flights.models import Flight, Reservation, Passenger


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
    passenger, _ = Passenger.objects.select_for_update() \
        .get_or_create(name=request.POST['name'], surname=request.POST['surname'])
    flight = Flight.objects.select_for_update().get(pk=request.POST['flight'])
    reservation, _ = Reservation.objects.select_for_update() \
        .get_or_create(passenger=passenger, flight=flight)
    reservation.ticketCount = request.POST['ticketCount']
    reservation.save()
    return redirect('details', request.POST['flight'])
