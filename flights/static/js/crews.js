'use strict';

const defaultStateContainer = {"Please wait": { title: "Fetching..." }};

const state = {
    flights: defaultStateContainer,
    crews: defaultStateContainer,
};

let isLoaded = false;


function updateFields() {
    if (isLoaded) {
        document.getElementById('crewSelection').innerHTML = createOptions(state.crews);
        document.getElementById('flightSelection').innerHTML = createOptions(state.flights);
        document.getElementById('crewFlights').innerHTML = createList(state.flights);
    }
}

function createList(resource) {
    return Object.keys(resource).filter(k => resource[k].crew).reduce(
        (acc, key) => acc + `<tr><th>${key}</th><td>${resource[key].title}</td></tr>`, ''
    )
}

function createOptions(resource) {
    return Object.keys(resource).reduce(
        (acc, key) => acc + `<option value=${key}>${resource[key].title}</option>`, ''
    )
}

function fetchResource (path, updateWith) {
    updateWith(defaultStateContainer);
    updateFields();
    const req = new XMLHttpRequest();
    req.open('GET', path);
    req.addEventListener('readystatechange', (event) => {
        if (req.readyState === 4 && req.status === 200) {
            console.log('done');
            updateWith(JSON.parse(req.response).response);
            updateFields();
        }
        // console.error(event);
    });
    req.send();

}

function formatDate(date) {
    if (!date.getFullYear) return date;
    return date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
}

function fetchFlights (date=new Date()) {
    console.log(formatDate(date));

    fetchResource(
        'http://localhost:8000/REST/flights?search=' + formatDate(date),
        (result) => { state.flights = result }
    );
}

function searchFlights(event) {
    event.preventDefault();
    fetchFlights(event.target.search.value);
}

function fetchCrews () {
    fetchResource(
        'http://localhost:8000/REST/crews',
        (result) => { state.crews = result }
    );
}

function setCrew(e) {
    const req = new XMLHttpRequest();
    const csrftoken = getCookie('csrftoken');

    e.preventDefault();

    req.open('POST', 'http://localhost:8000/REST/setCrew');
    req.withCredentials = true;
    req.setRequestHeader("X-CSRFToken", csrftoken);

    req.addEventListener('readystatechange', (event) => {
        if (req.readyState === 4) {
            if (req.status === 200) {
                fetchFlights();
            }
            else {
                console.error(req.response);
            }
        }
        // console.error(event);
    });

    req.send(JSON.stringify({crew: e.target.crewId.value, flight: e.target.flightId.value}));
    // req.send('dupa');
}

// Adapted from https://docs.djangoproject.com/en/2.0/ref/csrf/#ajax
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.onload = () => {
    isLoaded = true;
    updateFields();
    document.getElementById('flightForm').onsubmit = searchFlights;
    document.getElementById('crewForm').onsubmit = setCrew;
};

fetchFlights();
fetchCrews();
