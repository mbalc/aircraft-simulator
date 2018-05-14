from django.db import transaction
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template import loader
from django import forms
from django.views.decorators.http import require_POST

from flights.models import Airport, Flight, Reservation, Passenger

tpl_name = 'index.html'
tpl = loader.get_template('index.html')


# Create your views here.

def flights(request):
    dateQuery = request.GET.get('search')
    flightList = Flight.objects.order_by('takeoffTime', 'landingTime')
    if dateQuery:
        flightList = flightList.filter(takeoffTime__date__lte=dateQuery,
                                       landingTime__date__gte=dateQuery)

    return render(request, 'flights.html', locals())


def details(request, **kwargs):
    flight = get_object_or_404(Flight, pk=kwargs.get('pkey'))
    reservations = Reservation.objects.filter(flight=flight, ticketCount__gt=0).order_by('-updated')
    ticks = reservations.aggregate(total=Coalesce(Sum('ticketCount'), Value(0)))
    freeSeats = flight.plane.passengerLimit - ticks.get('total')

    return render(request, 'details.html', locals())

@transaction.atomic
@require_POST
def reserve(request):
    # print(request.POST['name'])
    # print(request.POST['surname'])
    # print(request.POST['ticketCount'])
    # print(request.POST['flight'])
    passenger, _ = Passenger.objects.get_or_create(name=request.POST['name'],
                                                   surname=request.POST['surname'])
    flight = Flight.objects.get(pk=request.POST['flight'])
    reservation, _ = Reservation.objects.get_or_create(passenger=passenger, flight=flight)
    reservation.ticketCount = request.POST['ticketCount']
    reservation.save()
    return redirect('details', request.POST['flight'])


def isShort(name):
    return len(name) < 5 and len != 'asdf'


class myForm(forms.Form):
    name = forms.CharField(validators=[isShort])


# fajne rzeczy: ModelForm, FormSet


def myErrorPage(request):
    if request.method == 'POST':
        f = myForm(request.POST)
        if f.is_valid():
            return HttpResponse('300')
        else:
            return HttpResponse(status='300')
    else:
        f = myForm()

    return render(request, tpl_name, {
        'form': f,
    })


class classView:
    def get(self, request):
        return HttpResponse('get blah')

    def post(self, request):
        return HttpResponse('post bleh')


def old(request):
    return HttpResponse("""
        <html>
        <body>
            <article>
            """
                        + str(request.META) +
                        """
                                </article>
                            </body>
                            </html>
                        """)
