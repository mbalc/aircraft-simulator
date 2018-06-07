"""Generate names for crew captains and add them to flight app database"""
from flights.models import Crew

CAPTAINS = [
    ['Andrew', 'Ryan'],
    ['Carol', 'Lowe'],
    ['Jo', 'Henderson'],
    ['Jessie', 'Taylor'],
    ['Alex', 'Hill'],
    ['Rory', 'Howard'],
    ['Erin', 'Cantrell'],
    ['Phoenix', 'Livingston'],
    ['Cameron', 'Soto'],
    ['Raylee', 'Adams'],
    ['Gabe', 'Chen'],
    ['Marley', 'Davis'],
    ['Clem', 'Foster'],
    ['Taylor', 'Burke'],
    ['Phoenix', 'Pearce'],
    ['Bev', 'Mills'],
    ['Brice', 'Frost'],
    ['Ashton', 'Strong'],
    ['Noel', 'Peters'],
    ['Jackie', 'Elliott'],
    ['Drew', 'Lawrence'],
]


def main():
    """Take care of all data generation"""
    # cleanup all models
    Crew.objects.all().delete()

    # init airports
    for [name, surname] in CAPTAINS:
        Crew.objects.create(cptName=name, cptSurname=surname)


main()
