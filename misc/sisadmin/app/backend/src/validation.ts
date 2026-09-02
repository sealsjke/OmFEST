import { z } from 'zod';
import { isValidIpv4, isValidMask } from './network/ipv4.js';

export const sessionParams = z.object({ sessionId: z.string().uuid() });
export const deviceParams = sessionParams.extend({ deviceId: z.string().uuid() });
export const linkParams = sessionParams.extend({ linkId: z.string().uuid() });
export const createDeviceBody = z.object({
  type: z.enum(['pc', 'switch', 'router']),
  x: z.number().finite().min(-10_000).max(10_000),
  y: z.number().finite().min(-10_000).max(10_000),
});
export const moveDeviceBody = z.object({ x: z.number().finite().min(-10_000).max(10_000), y: z.number().finite().min(-10_000).max(10_000) });
const endpoint = z.object({ deviceId: z.string().uuid(), interfaceId: z.string().min(1).max(40) });
export const createLinkBody = z.object({ a: endpoint, b: endpoint }).refine((value) => value.a.deviceId !== value.b.deviceId, 'Cannot connect a device to itself');
export const pcConfigBody = z.object({
  ip: z.string().refine(isValidIpv4, 'Invalid IPv4 address'),
  mask: z.string().refine(isValidMask, 'Invalid subnet mask'),
  gateway: z.string().refine(isValidIpv4, 'Invalid default gateway'),
});
export const commandBody = z.object({ command: z.string().max(200) });

