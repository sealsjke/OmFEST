import { randomUUID } from 'node:crypto';
import type { FastifyInstance, FastifyReply } from 'fastify';
import { ZodError } from 'zod';
import { executeRouterCommand } from '../cli/routerCli.js';
import { executeSwitchCommand } from '../cli/switchCli.js';
import { executePcCommand } from '../cli/pcCli.js';
import { prompt } from '../cli/common.js';
import { publicInstructions, challenge } from '../config/challenge.js';
import { validateChallenge } from '../network/challengeValidator.js';
import { getDevice, interfaceLink, toPublicState } from '../network/topology.js';
import { addDevice, createSession, findSession, resetSession, SessionCapacityError } from '../sessions/store.js';
import { commandBody, createDeviceBody, createLinkBody, deviceParams, linkParams, moveDeviceBody, pcConfigBody, sessionParams } from '../validation.js';

function positiveInteger(name: string, fallback: number): number {
  const value = Number(process.env[name] ?? fallback);
  return Number.isSafeInteger(value) && value > 0 ? value : fallback;
}

function badRequest(reply: FastifyReply, error: unknown) {
  const message = error instanceof ZodError ? error.issues[0]?.message : error instanceof Error ? error.message : 'Invalid request';
  return reply.code(400).send({ error: message ?? 'Invalid request' });
}

export async function apiRoutes(app: FastifyInstance): Promise<void> {
  app.get('/health', { config: { rateLimit: false } }, async () => ({ status: 'ok' }));
  app.get('/challenge', async () => publicInstructions);

  app.post('/session', {
    config: { rateLimit: { max: positiveInteger('SESSION_CREATE_RATE_LIMIT_PER_MINUTE', 120), timeWindow: '1 minute' } },
  }, async (request, reply) => {
    try {
      return reply.code(201).send(toPublicState(createSession(request.ip)));
    } catch (error) {
      if (error instanceof SessionCapacityError) {
        return reply.header('Retry-After', '60').code(error.scope === 'client' ? 429 : 503).send({ error: error.message });
      }
      return badRequest(reply, error);
    }
  });

  app.get('/session/:sessionId/state', async (request, reply) => {
    try {
      const { sessionId } = sessionParams.parse(request.params);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      return toPublicState(session);
    } catch (error) { return badRequest(reply, error); }
  });

  app.post('/session/:sessionId/device', async (request, reply) => {
    try {
      const { sessionId } = sessionParams.parse(request.params);
      const body = createDeviceBody.parse(request.body);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      addDevice(session, body.type, body.x, body.y);
      return reply.code(201).send(toPublicState(session));
    } catch (error) { return badRequest(reply, error); }
  });

  app.patch('/session/:sessionId/device/:deviceId', async (request, reply) => {
    try {
      const { sessionId, deviceId } = deviceParams.parse(request.params);
      const body = moveDeviceBody.parse(request.body);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      const device = getDevice(session, deviceId);
      if (!device) return reply.code(404).send({ error: 'Device not found' });
      device.x = body.x; device.y = body.y;
      return toPublicState(session);
    } catch (error) { return badRequest(reply, error); }
  });

  app.delete('/session/:sessionId/device/:deviceId', async (request, reply) => {
    try {
      const { sessionId, deviceId } = deviceParams.parse(request.params);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      if (!getDevice(session, deviceId)) return reply.code(404).send({ error: 'Device not found' });
      session.devices = session.devices.filter((device) => device.id !== deviceId);
      session.links = session.links.filter((link) => link.a.deviceId !== deviceId && link.b.deviceId !== deviceId);
      return toPublicState(session);
    } catch (error) { return badRequest(reply, error); }
  });

  app.post('/session/:sessionId/link', async (request, reply) => {
    try {
      const { sessionId } = sessionParams.parse(request.params);
      const body = createLinkBody.parse(request.body);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      const aDevice = getDevice(session, body.a.deviceId);
      const bDevice = getDevice(session, body.b.deviceId);
      if (!aDevice?.interfaces[body.a.interfaceId] || !bDevice?.interfaces[body.b.interfaceId]) throw new Error('Interface not found');
      if (interfaceLink(session, body.a.deviceId, body.a.interfaceId) || interfaceLink(session, body.b.deviceId, body.b.interfaceId)) throw new Error('Interface is already in use');
      session.links.push({ id: randomUUID(), a: body.a, b: body.b });
      return reply.code(201).send(toPublicState(session));
    } catch (error) { return badRequest(reply, error); }
  });

  app.delete('/session/:sessionId/link/:linkId', async (request, reply) => {
    try {
      const { sessionId, linkId } = linkParams.parse(request.params);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      if (!session.links.some((link) => link.id === linkId)) return reply.code(404).send({ error: 'Link not found' });
      session.links = session.links.filter((link) => link.id !== linkId);
      return toPublicState(session);
    } catch (error) { return badRequest(reply, error); }
  });

  app.post('/session/:sessionId/pc/:deviceId/config', async (request, reply) => {
    try {
      const { sessionId, deviceId } = deviceParams.parse(request.params);
      const body = pcConfigBody.parse(request.body);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      const device = getDevice(session, deviceId);
      if (!device || device.type !== 'pc') return reply.code(404).send({ error: 'PC not found' });
      const iface = device.interfaces.fa0!;
      iface.ip = body.ip; iface.mask = body.mask; device.defaultGateway = body.gateway;
      return toPublicState(session);
    } catch (error) { return badRequest(reply, error); }
  });

  app.post('/session/:sessionId/device/:deviceId/command', async (request, reply) => {
    try {
      const { sessionId, deviceId } = deviceParams.parse(request.params);
      const { command } = commandBody.parse(request.body);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      const device = getDevice(session, deviceId);
      if (!device) return reply.code(404).send({ error: 'Device not found' });
      let output = '';
      let exited = false;
      if (device.type === 'router') output = executeRouterCommand(session, device, command);
      else if (device.type === 'switch') output = executeSwitchCommand(session, device, command);
      else { const result = executePcCommand(session, device, command); output = result.output; exited = Boolean(result.exited); }

      const normalized = command.trim().replace(/\s+/g, ' ').toLowerCase();
      if (device.name === 'PC1' && normalized === `ping ${challenge.pc2.ip}`) {
        const validation = validateChallenge(session);
        if (validation.success) {
          const flag = process.env.FLAG ?? 'CTF{development_flag_not_configured}';
          output += `\r\n\r\nConnection established!\r\n\r\n${flag}`;
        } else app.log.debug({ sessionId, validationErrors: validation.errors }, 'Challenge validation failed');
      }
      return { output, prompt: prompt(device), clear: normalized === 'clear', exited, state: toPublicState(session) };
    } catch (error) { return badRequest(reply, error); }
  });

  app.post('/session/:sessionId/reset', async (request, reply) => {
    try {
      const { sessionId } = sessionParams.parse(request.params);
      const session = findSession(sessionId);
      if (!session) return reply.code(404).send({ error: 'Session not found' });
      resetSession(session);
      return toPublicState(session);
    } catch (error) { return badRequest(reply, error); }
  });
}
