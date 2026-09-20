import { getApiBaseUrl } from './constants';

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // Prevent trailing slash on /resources endpoint which causes 500
  if (!cleanEndpoint.startsWith('/resources')) {
    if (cleanEndpoint.includes('?')) {
      const [pathPart, queryPart] = cleanEndpoint.split('?');
      if (!pathPart.endsWith('/')) {
        cleanEndpoint = `${pathPart}/?${queryPart}`;
      }
    } else if (!cleanEndpoint.endsWith('/')) {
      cleanEndpoint = `${cleanEndpoint}/`;
    }
  }

  const url = `${baseUrl}${cleanEndpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error (${response.status}): ${errorText}`);
  }

  return response.json();
}
