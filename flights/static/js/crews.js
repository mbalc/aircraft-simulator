// eslint-disable-next-line import/extensions
import * as popup from './popup.js';

const defaultStateContainer = { 'Please wait': { title: 'Fetching...' } };

const state = {
  flights: defaultStateContainer,
  crews: defaultStateContainer,
  timeout: null,
};

const stateBackup = {};

let isLoaded = false;

function keysHaveKey(obj, requestedKey) {
  return Object.keys(obj).reduce((acc, key) => acc && obj[key][requestedKey]);
}

function backupState() {
  Object.keys(state).forEach((key) => { stateBackup[key] = state[key]; });
}

let updateFields; // func

function restoreState() {
  Object.keys(stateBackup).forEach((key) => { state[key] = stateBackup[key]; });
  updateFields();
}

function createOptions(resource) {
  if (resource && keysHaveKey(resource, 'title')) {
    return Object.keys(resource)
      .reduce((acc, key) => `${acc}<option value=${key}>${resource[key].title}</option>`, '');
  }
  popup.red('Faulty data received from server');
  restoreState();
  return '';
}

function createList(resource) {
  if (resource && keysHaveKey(resource, 'title')) {
    return Object.keys(resource)
      .filter(k => resource[k].crew) // only those that have a crew
      .reduce((acc, key) => `${acc}<tr><th>${key}</th><td>${resource[key].title}</td></tr>`, '');
  }
  popup.red('Faulty data received from server');
  restoreState();
  return '';
}

updateFields = () => {
  if (isLoaded) {
    document.getElementById('crewSelection').innerHTML = createOptions(state.crews);
    document.getElementById('flightSelection').innerHTML = createOptions(state.flights);
    document.getElementById('crewFlights').innerHTML = createList(state.flights);
  }
};

function fetchResource(path, updateWith) {
  try {
    backupState();
    updateWith(defaultStateContainer);
    updateFields();
  } catch (e) {
    popup.error(e);
  }

  const req = new XMLHttpRequest();
  req.open('GET', path);
  req.onreadystatechange = () => {
    try {
      if (req.readyState === 4) {
        if (req.status === 200) {
          updateWith(JSON.parse(req.response).response);
          updateFields();
        } else {
          restoreState();
          if (req.status === 404) {
            popup.e404();
          } else {
            popup.red('There was an issue with the refresh request\n - One probable' +
              ' cause of' +
              ' this might be the server being down');
          }
        }
      }
    } catch (e) {
      popup.error(e);
    }
  };
  try {
    req.send();
  } catch (err) {
    popup.error(err);
  }
}

function formatDate(date) {
  if (!date.getFullYear) return date;
  if (date === '') return new Date();
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
}

function fetchFlights(date = document.getElementById('dateInput').value || new Date()) {
  fetchResource(
    `/REST/flights?search=${formatDate(date)}`,
    (result) => { state.flights = result; },
  );
}

function fetchCrews() {
  fetchResource(
    '/REST/crews',
    (result) => { state.crews = result; },
  );
}

function searchFlights(event) {
  event.preventDefault();
  fetchFlights(event.target.search.value);
  fetchCrews();
}

// Adapted from https://docs.djangoproject.com/en/2.0/ref/csrf/#ajax
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i += 1) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (`${name}=`)) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function setCrew(e) {
  const req = new XMLHttpRequest();
  const csrftoken = getCookie('csrftoken');

  e.preventDefault();

  popup.hideStatus();

  req.open('POST', '/REST/setCrew');
  req.withCredentials = true;
  req.setRequestHeader('X-CSRFToken', csrftoken);

  req.onreadystatechange = () => {
    try {
      if (req.readyState === 4) {
        if (req.status === 200) {
          popup.status('Assignment successful!', 'rgba(32, 223, 32, 0.9)');
        } else if (req.status === 403) {
          popup.e403();
        } else if (req.status === 404) {
          popup.e404();
          return;
        } else if (req.status === 400) {
          popup.red(`You can't do such a change\n${req.getResponseHeader('error-message')}`);
        } else {
          popup.red(`There was an issue with the request\n${req.getResponseHeader('error-message') || 'An error occurred - maybe the server is down?'}`);
          return;
        }
        fetchFlights();
        fetchCrews();
      }
    } catch (err) {
      popup.error(err);
    }
  };
  try {
    req.send(JSON.stringify({ crew: e.target.crewId.value, flight: e.target.flightId.value }));
  } catch (err) {
    popup.error(err);
  }
}

window.onload = () => {
  isLoaded = true;
  fetchFlights();
  fetchCrews();
  document.getElementById('flightForm').onsubmit = searchFlights;
  document.getElementById('crewForm').onsubmit = setCrew;
};
