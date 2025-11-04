import { API_ROUTES } from './routes';

/** Error that contains HTTP status code and message. */
export class HttpError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly url: string,
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

/**
 * Performs a JSON request using the Fetch API and throws {@link HttpError} when the
 * response is not successful.
 */
export async function requestJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);

  if (!response.ok) {
    const message = `Request failed with status ${response.status}`;
    throw new HttpError(message, response.status, response.url);
  }

  return response.json() as Promise<T>;
}

/**
 * Helper for making POST requests with a JSON payload.
 */
export function postJson<TRequest, TResponse>(
  url: string,
  body: TRequest,
  init: RequestInit = {},
): Promise<TResponse> {
  return requestJson<TResponse>(url, {
    ...init,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
    body: JSON.stringify(body),
  });
}

export { API_ROUTES };
