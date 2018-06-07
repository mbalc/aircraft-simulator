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
    return Object.keys(resource).reduce(
        (acc, key) => acc + `<tr><th>${key}</th><td>${resource[key].title}</td></tr>`, ''
        // (key) => {
        //     console.log(key, resource[key]);
        //     return "<option>dupa</option>";
        // }
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

window.onload = () => {
    isLoaded = true;
    updateFields();
    document.getElementById('flightForm').onsubmit = searchFlights;
};

fetchFlights();
fetchCrews();
