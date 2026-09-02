import { randomUUID } from 'node:crypto';
import type { Device, DeviceType, LabSession, NetworkInterface } from '../models.js';

const sessions = new Map<string, LabSession>();
const sessionOwners = new Map<string, string>();

function positiveInteger(name: string, fallback: number): number {
  const value = Number(process.env[name] ?? fallback);
  return Number.isSafeInteger(value) && value > 0 ? value : fallback;
}

const ttl = positiveInteger('SESSION_TTL_MS', 7_200_000);
const maxSessions = positiveInteger('MAX_SESSIONS', 300);
const maxSessionsPerClient = positiveInteger('MAX_SESSIONS_PER_CLIENT', 120);

export class SessionCapacityError extends Error {
  constructor(public readonly scope: 'global' | 'client') {
    super(scope === 'global' ? 'The lab is currently at capacity' : 'Too many active sessions from this client');
    this.name = 'SessionCapacityError';
  }
}

function interfacesFor(type: DeviceType): Record<string, NetworkInterface> {
  const definitions = type === 'pc'
    ? [['fa0', 'FastEthernet0']]
    : type === 'router'
      ? [['g0/0', 'GigabitEthernet0/0'], ['g0/1', 'GigabitEthernet0/1']]
      : Array.from({ length: 4 }, (_, index) => [`fa0/${index + 1}`, `FastEthernet0/${index + 1}`]);
  return Object.fromEntries(definitions.map(([id, name]) => [id, { id, name, ip: null, mask: null, adminUp: type !== 'router' }]));
}

export function createSession(ownerKey: string): LabSession {
  cleanupExpiredSessions();
  if (sessions.size >= maxSessions) throw new SessionCapacityError('global');
  let ownedSessions = 0;
  for (const owner of sessionOwners.values()) if (owner === ownerKey) ownedSessions += 1;
  if (ownedSessions >= maxSessionsPerClient) throw new SessionCapacityError('client');

  const now = Date.now();
  const session: LabSession = { id: randomUUID(), devices: [], links: [], createdAt: now, touchedAt: now };
  sessions.set(session.id, session);
  sessionOwners.set(session.id, ownerKey);
  return session;
}

export function findSession(id: string): LabSession | undefined {
  const session = sessions.get(id);
  if (session) session.touchedAt = Date.now();
  return session;
}

export function resetSession(session: LabSession): void {
  session.devices = [];
  session.links = [];
  session.touchedAt = Date.now();
}

export function addDevice(session: LabSession, type: DeviceType, x: number, y: number): Device {
  const limit = type === 'router' ? 1 : 2;
  const existing = session.devices.filter((device) => device.type === type);
  if (existing.length >= limit) throw new Error(`Maximum ${limit} ${type} device(s) allowed`);
  const prefix = type === 'pc' ? 'PC' : type === 'switch' ? 'SW' : 'R';
  const used = new Set(existing.map((device) => Number(device.name.slice(prefix.length))));
  let number = 1;
  while (used.has(number)) number += 1;
  const device: Device = {
    id: randomUUID(), type, name: `${prefix}${number}`, x, y, interfaces: interfacesFor(type), defaultGateway: null,
    cli: { mode: 'USER_EXEC', selectedInterface: null },
  };
  session.devices.push(device);
  return device;
}

export function cleanupExpiredSessions(): void {
  const cutoff = Date.now() - ttl;
  for (const [id, session] of sessions) if (session.touchedAt < cutoff) {
    sessions.delete(id);
    sessionOwners.delete(id);
  }
}

export function startCleanup(): NodeJS.Timeout {
  const timer = setInterval(cleanupExpiredSessions, Math.min(ttl, 300_000));
  timer.unref();
  return timer;
}
