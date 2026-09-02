import type { Device, LabSession } from '../models.js';
import { isValidIpv4, isValidMask } from '../network/ipv4.js';
import { interfaceIsUp } from '../network/topology.js';
import { simulatePing } from '../network/simulator.js';
import { invalid, normalizeInterface } from './common.js';

function status(session: LabSession, device: Device): string {
  const header = 'Interface              IP-Address      OK? Method Status                Protocol';
  const rows = Object.values(device.interfaces).map((iface) => {
    const physical = interfaceIsUp(session, device.id, iface.id);
    const state = !iface.adminUp ? 'administratively down' : physical ? 'up' : 'down';
    const protocol = physical ? 'up' : 'down';
    return `${iface.name.padEnd(23)}${(iface.ip ?? 'unassigned').padEnd(16)}YES manual ${state.padEnd(22)}${protocol}`;
  });
  return [header, ...rows].join('\r\n');
}

function runningConfig(device: Device): string {
  const lines = ['Building configuration...', '', 'Current configuration:', '!', `hostname ${device.name}`];
  for (const iface of Object.values(device.interfaces)) {
    lines.push(`interface ${iface.name}`, iface.ip && iface.mask ? ` ip address ${iface.ip} ${iface.mask}` : ' no ip address', iface.adminUp ? ' no shutdown' : ' shutdown', '!');
  }
  return lines.join('\r\n');
}

export function executeRouterCommand(session: LabSession, device: Device, raw: string): string {
  const command = raw.trim().replace(/\s+/g, ' ');
  const lower = command.toLowerCase();
  if (!command) return '';
  if (lower === 'help' || lower === '?') return 'enable, configure terminal, interface, ip address, shutdown, no shutdown, show, ping, exit, end, clear';
  if (lower === 'clear') return '';
  if (lower === 'end' && device.cli.mode !== 'USER_EXEC') { device.cli.mode = 'PRIVILEGED_EXEC'; device.cli.selectedInterface = null; return ''; }
  if (lower === 'exit') {
    if (device.cli.mode === 'INTERFACE_CONFIG') device.cli.mode = 'GLOBAL_CONFIG';
    else if (device.cli.mode === 'GLOBAL_CONFIG') device.cli.mode = 'PRIVILEGED_EXEC';
    else if (device.cli.mode === 'PRIVILEGED_EXEC') device.cli.mode = 'USER_EXEC';
    return '';
  }
  if (device.cli.mode === 'USER_EXEC') {
    if (lower === 'enable') { device.cli.mode = 'PRIVILEGED_EXEC'; return ''; }
    if (lower.startsWith('ping ')) return simulatePing(session, device.id, command.slice(5).trim()).output;
    return invalid;
  }
  if (device.cli.mode === 'PRIVILEGED_EXEC') {
    if (lower === 'configure terminal' || lower === 'conf t') { device.cli.mode = 'GLOBAL_CONFIG'; return 'Enter configuration commands, one per line. End with CNTL/Z.'; }
    if (lower === 'show ip interface brief') return status(session, device);
    if (lower === 'show running-config' || lower === 'show run') return runningConfig(device);
    if (lower.startsWith('ping ')) return simulatePing(session, device.id, command.slice(5).trim()).output;
    return invalid;
  }
  if (device.cli.mode === 'GLOBAL_CONFIG') {
    if (lower.startsWith('interface ')) {
      const iface = normalizeInterface(command.slice(command.indexOf(' ') + 1));
      if (!iface || !device.interfaces[iface]) return invalid;
      device.cli.mode = 'INTERFACE_CONFIG'; device.cli.selectedInterface = iface; return '';
    }
    return invalid;
  }
  const iface = device.cli.selectedInterface ? device.interfaces[device.cli.selectedInterface] : undefined;
  if (!iface) { device.cli.mode = 'GLOBAL_CONFIG'; return invalid; }
  if (lower === 'shutdown') { iface.adminUp = false; return ''; }
  if (lower === 'no shutdown') { iface.adminUp = true; return ''; }
  if (lower.startsWith('ip address ')) {
    const [, , ip, mask] = command.split(' ');
    if (!ip || !mask || !isValidIpv4(ip) || !isValidMask(mask)) return invalid;
    iface.ip = ip; iface.mask = mask; return '';
  }
  if (lower === 'no ip address') { iface.ip = null; iface.mask = null; return ''; }
  return invalid;
}

