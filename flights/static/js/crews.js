const defaultStateContainer = { 'Please wait': { title: 'Fetching...' } };

const state = {
  flights: defaultStateContainer,
  crews: defaultStateContainer,
  timeout: null,
};

let isLoaded = false;

function createList(resource) {
  return Object.keys(resource).filter(k => resource[k].crew).reduce((acc, key) => `${acc}<tr><th>${key}</th><td>${resource[key].title}</td></tr>`, '');
}

function createOptions(resource) {
  return Object.keys(resource).reduce((acc, key) => `${acc}<option value=${key}>${resource[key].title}</option>`, '');
}

function updateFields() {
  if (isLoaded) {
    document.getElementById('crewSelection').innerHTML = createOptions(state.crews);
    document.getElementById('flightSelection').innerHTML = createOptions(state.flights);
    document.getElementById('crewFlights').innerHTML = createList(state.flights);
  }
}

function hideStatus() {
  document.getElementById('request-status').style.visibility = 'hidden';
}

function triggerStatusPopup(innerText, color) {
  const status = document.getElementById('request-status');
  window.clearTimeout(state.timeout);
  status.innerText = innerText;
  status.style.background = color;
  status.style.visibility = 'visible';
  state.timeout = setTimeout(hideStatus, 5000);
  status.onclick = hideStatus;
}

function triggerRedPopup(message) {
  triggerStatusPopup(message, 'rgba(223, 32, 32, 0.9)');
}

function popup404() {
  triggerRedPopup('Server did not respond for the request!');
}

function popup403() {
  triggerRedPopup('You are not allowed to do this\nPlease login via main page');
}

function popupError(e) {
  triggerRedPopup('Something went terribly wrong...\nSee dev console for details');
  throw e;
}

function fetchResource(path, updateWith) {
  try {
    updateWith(defaultStateContainer);
    updateFields();
  } catch (e) {
    popupError(e);
  }

  const req = new XMLHttpRequest();
  req.open('GET', path);
  req.addEventListener('readystatechange', () => {
    try {
      if (req.readyState === 4 && req.status > 100) {
        if (req.status === 200) {
          updateWith(JSON.parse(req.response).response);
          updateFields();
        } else if (req.status === 404) {
          popup404();
        } else {
          triggerRedPopup('Server did not respond for the request!');
        }
      }
    } catch (e) {
      popupError(e);
    }
  });
  req.send();
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

function searchFlights(event) {
  event.preventDefault();
  fetchFlights(event.target.search.value);
}

function fetchCrews() {
  fetchResource(
    '/REST/crews',
    (result) => { state.crews = result; },
  );
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

  hideStatus();

  req.open('POST', '/REST/setCrew');
  req.withCredentials = true;
  req.setRequestHeader('X-CSRFToken', csrftoken);

  req.addEventListener('readystatechange', () => {
    try {
      if (req.readyState === 4 && req.status > 100) {
        if (req.status === 200) {
          triggerStatusPopup('Assignment successful!', 'rgba(32, 223, 32, 0.9)');
        } else if (req.status === 403) {
          popup403();
        } else if (req.status === 404) {
          popup404();
          return;
        } else if (req.status === 400) {
          triggerRedPopup(`You can't do such a change\n${req.getResponseHeader('error-message')}`);
        } else {
          triggerRedPopup(`There was an issue with the request\n${req.getResponseHeader('error-message') || 'An error occurred'}`);
        }
        fetchFlights();
      }
    } catch (err) {
      popupError(err);
    }
  });

  req.send(JSON.stringify({ crew: e.target.crewId.value, flight: e.target.flightId.value }));
}

window.onload = () => {
  isLoaded = true;
  updateFields();
  document.getElementById('flightForm').onsubmit = searchFlights;
  document.getElementById('crewForm').onsubmit = setCrew;
};

fetchFlights(new Date());
fetchCrews();
