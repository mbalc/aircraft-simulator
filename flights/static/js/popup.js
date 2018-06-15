let lastTimeout = 0;
export function hideStatus() {
  document.getElementById('request-status').style.visibility = 'hidden';
}

export function status(innerText, color) {
  const statObj = document.getElementById('request-status');
  window.clearTimeout(lastTimeout);
  statObj.innerText = innerText;
  statObj.style.background = color;
  statObj.style.visibility = 'visible';
  lastTimeout = setTimeout(hideStatus, 5000);
  statObj.onclick = hideStatus;
}

export function red(message) {
  status(message, 'rgba(223, 32, 32, 0.9)');
}

export function e404() {
  red('Server did not respond for the request!');
}

export function e403() {
  red('You are not allowed to do this\nPlease login via main page');
}

export function timeout() {
  red('Request timed out');
}

export function error(e) {
  red('Something went terribly wrong...\nSee dev console for details');
  // eslint-disable-next-line no-console
  console.error(e);
}

