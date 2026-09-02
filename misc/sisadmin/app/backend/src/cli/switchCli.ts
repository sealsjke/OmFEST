import type { Device, LabSession } from '../models.js';
import { interfaceIsUp } from '../network/topology.js';
import { invalid, normalizeInterface } from './common.js';

function interfacesStatus(session: LabSession, device: Device): string {
  const rows = Object.values(device.interfaces).map((iface) => `${iface.name.padEnd(22)}${interfaceIsUp(session, device.id, iface.id) ? 'connected' : iface.adminUp ? 'notconnect' : 'disabled'}  1     auto   auto  10/100BaseTX`);
  return ['Port                  Status       Vlan  Duplex Speed Type', ...rows].join('\r\n');
}

function runningConfig(device: Device): string {
  return ['Building configuration...', '!', `hostname ${device.name}`, ...Object.values(device.interfaces).flatMap((iface) => [`interface ${iface.name}`, iface.adminUp ? ' no shutdown' : ' shutdown', '!'])].join('\r\n');
}

export function executeSwitchCommand(session: LabSession, device: Device, raw: string): string {
  const command = raw.trim().replace(/\s+/g, ' ');
  const lower = command.toLowerCase();
  if (!command || lower === 'clear') return '';
  if (lower === 'help' || lower === '?') return 'enable, configure terminal, interface, shutdown, no shutdown, show interfaces status, show running-config, exit, end, clear';
  if (lower === 'end' && device.cli.mode !== 'USER_EXEC') { device.cli.mode = 'PRIVILEGED_EXEC'; device.cli.selectedInterface = null; return ''; }
  if (lower === 'exit') {
    if (device.cli.mode === 'INTERFACE_CONFIG') device.cli.mode = 'GLOBAL_CONFIG';
    else if (device.cli.mode === 'GLOBAL_CONFIG') device.cli.mode = 'PRIVILEGED_EXEC';
    else if (device.cli.mode === 'PRIVILEGED_EXEC') device.cli.mode = 'USER_EXEC';
    return '';
  }
  if (device.cli.mode === 'USER_EXEC') {
    if (lower === 'enable') { device.cli.mode = 'PRIVILEGED_EXEC'; return ''; }
    return invalid;
  }
  if (device.cli.mode === 'PRIVILEGED_EXEC') {
    if (lower === 'configure terminal' || lower === 'conf t') { device.cli.mode = 'GLOBAL_CONFIG'; return 'Enter configuration commands, one per line. End with CNTL/Z.'; }
    if (lower === 'show interfaces status') return interfacesStatus(session, device);
    if (lower === 'show running-config' || lower === 'show run') return runningConfig(device);
    return invalid;
  }
  if (device.cli.mode === 'GLOBAL_CONFIG') {
    if (!lower.startsWith('interface ')) return invalid;
    const id = normalizeInterface(command.slice(command.indexOf(' ') + 1));
    if (!id || !device.interfaces[id]) return invalid;
    device.cli.mode = 'INTERFACE_CONFIG'; device.cli.selectedInterface = id; return '';
  }
  const iface = device.cli.selectedInterface ? device.interfaces[device.cli.selectedInterface] : undefined;
  if (!iface) return invalid;
  if (lower === 'shutdown') { iface.adminUp = false; return ''; }
  if (lower === 'no shutdown') { iface.adminUp = true; return ''; }
  return invalid;
}

