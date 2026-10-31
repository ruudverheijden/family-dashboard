import { uuid } from './helpers.js';

export async function api(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-Family-Request': '1',
        ...options.headers
      }
    });
  } catch {
    const error = new Error('Geen verbinding. Je wijziging is niet bevestigd. Probeer opnieuw.');
    error.networkError = true;
    throw error;
  }
  let result;
  try {
    result = await response.json();
  } catch {
    const error = new Error('De server geeft geen geldig antwoord. Probeer opnieuw.');
    if (!response.ok) error.status = response.status;
    throw error;
  }
  if (!response.ok) {
    const error = new Error(
      typeof result.detail === 'string' ? result.detail : 'Controleer de ingevulde gegevens.'
    );
    error.status = response.status;
    throw error;
  }
  return result;
}
export async function mutate(kind, item, body, action = 'save', requestId = uuid()) {
  return api('/api/entities/' + kind, {
    method: 'POST',
    body: JSON.stringify({
      request_id: requestId,
      id: item?.id || uuid(),
      version: item?.version || 0,
      action,
      body
    })
  });
}
