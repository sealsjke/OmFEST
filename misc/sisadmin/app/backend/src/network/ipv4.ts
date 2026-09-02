export function ipv4ToInt(ip: string): number {
  const parts = ip.split('.');
  if (parts.length !== 4 || parts.some((part) => !/^\d{1,3}$/.test(part) || Number(part) > 255)) {
    throw new Error('Invalid IPv4 address');
  }
  return parts.reduce((value, part) => ((value << 8) | Number(part)) >>> 0, 0) >>> 0;
}

export function intToIpv4(value: number): string {
  const unsigned = value >>> 0;
  return [unsigned >>> 24, (unsigned >>> 16) & 255, (unsigned >>> 8) & 255, unsigned & 255].join('.');
}

export function isValidIpv4(ip: string): boolean {
  try { ipv4ToInt(ip); return true; } catch { return false; }
}

export function maskToPrefix(mask: string): number {
  const value = ipv4ToInt(mask);
  let seenZero = false;
  let prefix = 0;
  for (let bit = 31; bit >= 0; bit -= 1) {
    const one = ((value >>> bit) & 1) === 1;
    if (!one) seenZero = true;
    else if (seenZero) throw new Error('Non-contiguous subnet mask');
    else prefix += 1;
  }
  return prefix;
}

export function isValidMask(mask: string): boolean {
  try { const prefix = maskToPrefix(mask); return prefix >= 1 && prefix <= 30; } catch { return false; }
}

export function networkAddress(ip: string, mask: string): string {
  return intToIpv4((ipv4ToInt(ip) & ipv4ToInt(mask)) >>> 0);
}

export function isSameSubnet(first: string, second: string, mask: string): boolean {
  return networkAddress(first, mask) === networkAddress(second, mask);
}

