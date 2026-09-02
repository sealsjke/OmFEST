import Fastify from 'fastify';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import { apiRoutes } from './routes/api.js';

function positiveInteger(name: string, fallback: number): number {
  const value = Number(process.env[name] ?? fallback);
  return Number.isSafeInteger(value) && value > 0 ? value : fallback;
}

export async function buildApp() {
  const app = Fastify({
    logger: { level: process.env.LOG_LEVEL ?? 'info' },
    bodyLimit: 16 * 1024,
    requestTimeout: 10_000,
    // The backend is reachable only from the bundled Nginx container, which
    // overwrites X-Forwarded-For instead of accepting a client-supplied value.
    trustProxy: true,
  });
  await app.register(helmet, { contentSecurityPolicy: false });
  await app.register(rateLimit, {
    max: positiveInteger('API_RATE_LIMIT_PER_MINUTE', 1_500),
    timeWindow: '1 minute',
    cache: 10_000,
  });
  await app.register(apiRoutes, { prefix: '/api' });
  app.setNotFoundHandler(async (_request, reply) => reply.code(404).send({ error: 'Not found' }));
  return app;
}
