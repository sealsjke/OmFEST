import type { Device, LabSession, NetworkInterface } from '../models.js';
import { isSameSubnet, isValidIpv4, isValidMask, networkAddress } from './ipv4.js';
import { getDevice, hasLayer2Path, interfaceIsUp } from './topology.js';

export interface PingResult { success: boolean; reason: string; output: string }

type LocatedInterface = { device: Device; iface: NetworkInterface };

export function findDeviceByIp(session: LabSession, ip: string): LocatedInterface | null {
  const matches: LocatedInterface[] = [];
  for (const device of session.devices) {
    for (const iface of Object.values(device.interfaces)) if (iface.ip === ip) matches.push({ device, iface });
  }
  return matches.length === 1 ? matches[0]! : null;
}

function usable(session: LabSession, device: Device, iface: NetworkInterface): boolean {
  return Boolean(iface.ip && iface.mask && isValidIpv4(iface.ip) && isValidMask(iface.mask) && iface.adminUp && interfaceIsUp(session, device.id, iface.id));
}

function duplicateIps(session: LabSession): boolean {
  const seen = new Set<string>();
  for (const device of session.devices) for (const iface of Object.values(device.interfaces)) {
    if (!iface.ip) continue;
    if (seen.has(iface.ip)) return true;
    seen.add(iface.ip);
  }
  return false;
}

function reachableOneWay(session: LabSession, source: Device, destination: LocatedInterface): { ok: boolean; reason: string } {
  const sourceInterfaces = Object.values(source.interfaces).filter((iface) => usable(session, source, iface));
  if (!sourceInterfaces.length) return { ok: false, reason: 'source interface is down or unconfigured' };

  for (const sourceIface of sourceInterfaces) {
    if (sourceIface.ip && sourceIface.mask && isSameSubnet(sourceIface.ip, destination.iface.ip!, sourceIface.mask) &&
        usable(session, destination.device, destination.iface) && hasLayer2Path(session, source.id, destination.device.id)) {
      return { ok: true, reason: 'directly connected' };
    }
  }

  if (source.type === 'router') return { ok: false, reason: 'router has no directly connected route' };
  if (!source.defaultGateway || !isValidIpv4(source.defaultGateway)) return { ok: false, reason: 'default gateway missing' };
  const sourceIface = sourceInterfaces[0]!;
  if (!sourceIface.ip || !sourceIface.mask || !isSameSubnet(sourceIface.ip, source.defaultGateway, sourceIface.mask)) {
    return { ok: false, reason: 'gateway is outside source subnet' };
  }
  const gateway = findDeviceByIp(session, source.defaultGateway);
  if (!gateway || gateway.device.type !== 'router' || !usable(session, gateway.device, gateway.iface) || !hasLayer2Path(session, source.id, gateway.device.id)) {
    return { ok: false, reason: 'gateway is unreachable' };
  }
  const route = Object.values(gateway.device.interfaces).find((iface) => iface.ip && iface.mask && usable(session, gateway.device, iface) &&
    networkAddress(iface.ip, iface.mask) === networkAddress(destination.iface.ip!, destination.iface.mask!));
  if (!route || !hasLayer2Path(session, gateway.device.id, destination.device.id) || !usable(session, destination.device, destination.iface)) {
    return { ok: false, reason: 'no connected route to destination' };
  }
  return { ok: true, reason: 'routed' };
}

function pingText(target: string, success: boolean): string {
  const lines = success
    ? Array(4).fill(`Reply from ${target}: bytes=32 time<1ms TTL=127`)
    : Array(4).fill('Request timed out.');
  return [`Pinging ${target} with 32 bytes of data:`, '', ...lines, '', `Ping statistics for ${target}:`,
    success ? '    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)' : '    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)'].join('\r\n');
}

export function simulatePing(session: LabSession, sourceId: string, targetIp: string): PingResult {
  const source = getDevice(session, sourceId);
  if (!source || !isValidIpv4(targetIp)) return { success: false, reason: 'invalid source or target', output: pingText(targetIp, false) };
  if (duplicateIps(session)) return { success: false, reason: 'duplicate IP address', output: pingText(targetIp, false) };
  const destination = findDeviceByIp(session, targetIp);
  if (!destination?.iface.mask || !isValidMask(destination.iface.mask)) return { success: false, reason: 'destination not found', output: pingText(targetIp, false) };
  const forward = reachableOneWay(session, source, destination);
  if (!forward.ok) return { success: false, reason: forward.reason, output: pingText(targetIp, false) };
  const sourceIp = Object.values(source.interfaces).find((iface) => iface.ip)?.ip;
  if (!sourceIp) return { success: false, reason: 'source IP missing', output: pingText(targetIp, false) };
  const sourceLocated = findDeviceByIp(session, sourceIp);
  const reverse = sourceLocated ? reachableOneWay(session, destination.device, sourceLocated) : { ok: false, reason: 'source missing' };
  const success = reverse.ok;
  return { success, reason: success ? 'reachable' : `reply path: ${reverse.reason}`, output: pingText(targetIp, success) };
}

