import type { Device, LabSession } from '../models.js';
import { simulatePing } from '../network/simulator.js';

export interface PcCommandResult { output: string; exited?: boolean }

export function executePcCommand(session: LabSession, device: Device, raw: string): PcCommandResult {
  const command = raw.trim().replace(/\s+/g, ' ');
  const lower = command.toLowerCase();
  const iface = device.interfaces.fa0!;
  if (!command || lower === 'clear') return { output: '' };
  if (lower === 'help') return { output: 'Supported commands: ipconfig, ipconfig /all, ping <ip>, help, clear, exit' };
  if (lower === 'exit') return { output: '', exited: true };
  if (lower === 'ipconfig' || lower === 'ipconfig /all') return { output: [
    'FastEthernet0 Connection:', '', `   IPv4 Address. . . . . . . . . . : ${iface.ip ?? '0.0.0.0'}`,
    `   Subnet Mask . . . . . . . . . : ${iface.mask ?? '0.0.0.0'}`,
    `   Default Gateway . . . . . . . : ${device.defaultGateway ?? '0.0.0.0'}`,
    `   Media State . . . . . . . . . : ${iface.adminUp ? 'Media connected' : 'Media disconnected'}`,
  ].join('\r\n') };
  if (lower.startsWith('ping ')) return { output: simulatePing(session, device.id, command.slice(5).trim()).output };
  return { output: `'${command}' is not recognized as an internal or external command.` };
}

