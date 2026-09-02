import type { Device, LabSession, Link, NetworkInterface, PublicState } from '../models.js';

export function getDevice(session: LabSession, id: string): Device | undefined {
  return session.devices.find((device) => device.id === id);
}

export function getInterface(session: LabSession, deviceId: string, interfaceId: string): NetworkInterface | undefined {
  return getDevice(session, deviceId)?.interfaces[interfaceId];
}

export function linkIsUp(session: LabSession, link: Link): boolean {
  const left = getInterface(session, link.a.deviceId, link.a.interfaceId);
  const right = getInterface(session, link.b.deviceId, link.b.interfaceId);
  return Boolean(left?.adminUp && right?.adminUp);
}

export function interfaceLink(session: LabSession, deviceId: string, interfaceId: string): Link | undefined {
  return session.links.find((link) =>
    (link.a.deviceId === deviceId && link.a.interfaceId === interfaceId) ||
    (link.b.deviceId === deviceId && link.b.interfaceId === interfaceId));
}

export function interfaceIsUp(session: LabSession, deviceId: string, interfaceId: string): boolean {
  const link = interfaceLink(session, deviceId, interfaceId);
  return Boolean(link && linkIsUp(session, link));
}

export function otherEndpoint(link: Link, deviceId: string) {
  return link.a.deviceId === deviceId ? link.b : link.a;
}

export function buildAdjacencyGraph(session: LabSession, onlyUp = true): Map<string, string[]> {
  const graph = new Map<string, string[]>(session.devices.map((device) => [device.id, []]));
  for (const link of session.links) {
    if (onlyUp && !linkIsUp(session, link)) continue;
    graph.get(link.a.deviceId)?.push(link.b.deviceId);
    graph.get(link.b.deviceId)?.push(link.a.deviceId);
  }
  return graph;
}

export function findPhysicalPath(session: LabSession, sourceId: string, destinationId: string, onlyUp = true): string[] | null {
  const graph = buildAdjacencyGraph(session, onlyUp);
  const queue: string[][] = [[sourceId]];
  const seen = new Set([sourceId]);
  while (queue.length) {
    const path = queue.shift()!;
    const current = path[path.length - 1]!;
    if (current === destinationId) return path;
    for (const next of graph.get(current) ?? []) {
      if (!seen.has(next)) { seen.add(next); queue.push([...path, next]); }
    }
  }
  return null;
}

export function hasLayer2Path(session: LabSession, sourceId: string, destinationId: string): boolean {
  const path = findPhysicalPath(session, sourceId, destinationId, true);
  if (!path) return false;
  return path.slice(1, -1).every((id) => getDevice(session, id)?.type === 'switch');
}

export function toPublicState(session: LabSession): PublicState {
  return {
    id: session.id,
    devices: session.devices.map(({ cli: _cli, ...device }) => ({
      ...device,
      interfaces: Object.fromEntries(Object.entries(device.interfaces).map(([id, iface]) => [id, {
        ...iface,
        linkUp: interfaceIsUp(session, device.id, id),
      }])),
    })),
    links: session.links.map((link) => ({ ...link, up: linkIsUp(session, link) })),
  };
}

