import type { Device } from '../models.js';

export function prompt(device: Device): string {
  const base = device.type === 'router' ? 'Router' : device.type === 'switch' ? 'Switch' : 'C:\\>';
  if (device.type === 'pc') return base;
  if (device.cli.mode === 'USER_EXEC') return `${base}>`;
  if (device.cli.mode === 'PRIVILEGED_EXEC') return `${base}#`;
  if (device.cli.mode === 'GLOBAL_CONFIG') return `${base}(config)#`;
  return `${base}(config-if)#`;
}

export const invalid = "% Invalid input detected at '^' marker.";

export function normalizeInterface(value: string): string | null {
  const normalized = value.toLowerCase().replace(/\s+/g, '');
  const aliases: Record<string, string> = {
    'g0/0': 'g0/0', 'gigabitethernet0/0': 'g0/0',
    'g0/1': 'g0/1', 'gigabitethernet0/1': 'g0/1',
    'fa0/1': 'fa0/1', 'fastethernet0/1': 'fa0/1',
    'fa0/2': 'fa0/2', 'fastethernet0/2': 'fa0/2',
    'fa0/3': 'fa0/3', 'fastethernet0/3': 'fa0/3',
    'fa0/4': 'fa0/4', 'fastethernet0/4': 'fa0/4',
  };
  return aliases[normalized] ?? null;
}

