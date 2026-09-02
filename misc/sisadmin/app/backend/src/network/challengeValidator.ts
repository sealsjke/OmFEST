import { challenge } from '../config/challenge.js';
import type { Device, LabSession } from '../models.js';
import { simulatePing } from './simulator.js';
import { findPhysicalPath, getDevice, interfaceIsUp } from './topology.js';

export interface ValidationResult { success: boolean; errors: string[] }

function matchesPc(device: Device | undefined, expected: { ip: string; mask: string; gateway: string }): boolean {
  const iface = device?.interfaces.fa0;
  return Boolean(device?.type === 'pc' && iface?.ip === expected.ip && iface.mask === expected.mask &&
    device.defaultGateway === expected.gateway && iface.adminUp);
}

export function validateChallenge(session: LabSession): ValidationResult {
  const errors: string[] = [];
  const pc1 = session.devices.find((device) => device.name === 'PC1');
  const pc2 = session.devices.find((device) => device.name === 'PC2');
  const sw1 = session.devices.find((device) => device.name === 'SW1');
  const sw2 = session.devices.find((device) => device.name === 'SW2');
  const router = session.devices.find((device) => device.name === 'R1');
  if (session.devices.length !== 5 || session.links.length !== 4) errors.push('unexpected device or link count');
  if (!matchesPc(pc1, challenge.pc1)) errors.push('PC1 addressing mismatch');
  if (!matchesPc(pc2, challenge.pc2)) errors.push('PC2 addressing mismatch');
  if (!sw1 || sw1.type !== 'switch' || !sw2 || sw2.type !== 'switch') errors.push('switch roles missing');
  if (!router || router.type !== 'router') errors.push('router missing');
  if (router) {
    for (const id of ['g0/0', 'g0/1'] as const) {
      const iface = router.interfaces[id];
      const expected = challenge.router[id];
      if (!iface || iface.ip !== expected.ip || iface.mask !== expected.mask || !iface.adminUp || !interfaceIsUp(session, router.id, id)) {
        errors.push(`${id} mismatch or down`);
      }
    }
  }
  if (pc1 && pc2) {
    const path = findPhysicalPath(session, pc1.id, pc2.id, true);
    const expectedPath = [pc1.id, sw1?.id, router?.id, sw2?.id, pc2.id];
    if (!path || path.length !== 5 || path.some((id, index) => id !== expectedPath[index])) errors.push('physical topology mismatch');
    if (!simulatePing(session, pc1.id, challenge.pc2.ip).success) errors.push('end-to-end ping failed');
  }
  return { success: errors.length === 0, errors };
}
