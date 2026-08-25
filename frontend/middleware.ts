import { next } from '@vercel/functions';

const REALM = 'Tourism Route Planner';

function unauthorized() {
  return new Response('Authentication required.', {
    status: 401,
    headers: {
      'WWW-Authenticate': `Basic realm="${REALM}"`,
    },
  });
}

export default function middleware(request: Request) {
  const user = process.env.BASIC_AUTH_USER;
  const password = process.env.BASIC_AUTH_PASSWORD;

  if (!user || !password) {
    return new Response('Basic auth is not configured.', { status: 500 });
  }

  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Basic ')) {
    return unauthorized();
  }

  const decoded = atob(authHeader.slice('Basic '.length));
  const separatorIndex = decoded.indexOf(':');
  const inputUser = decoded.slice(0, separatorIndex);
  const inputPassword = decoded.slice(separatorIndex + 1);

  if (inputUser !== user || inputPassword !== password) {
    return unauthorized();
  }

  return next();
}
