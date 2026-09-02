export type DeviceType = 'pc' | 'switch' | 'router';

export interface NetworkInterface {
  id: string;
  name: string;
  ip: string | null;
  mask: string | null;
  adminUp: boolean;
  linkUp: boolean;
}

export interface Device {
  id: string;
  type: DeviceType;
  name: string;
  x: number;
  y: number;
  interfaces: Record<string, NetworkInterface>;
  defaultGateway: string | null;
}

export interface Endpoint { deviceId: string; interfaceId: string }
export interface Link { id: string; a: Endpoint; b: Endpoint; up: boolean }
export interface LabState { id: string; devices: Device[]; links: Link[] }
export interface AddressRow { device: string; interface: string; ip: string; mask: string; gateway: string }
export interface Instructions { title: string; objective: string; addressing: AddressRow[] }

