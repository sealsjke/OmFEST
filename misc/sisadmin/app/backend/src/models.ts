export type DeviceType = 'pc' | 'switch' | 'router';
export type CliMode = 'USER_EXEC' | 'PRIVILEGED_EXEC' | 'GLOBAL_CONFIG' | 'INTERFACE_CONFIG';

export interface NetworkInterface {
  id: string;
  name: string;
  ip: string | null;
  mask: string | null;
  adminUp: boolean;
}

export interface Device {
  id: string;
  type: DeviceType;
  name: string;
  x: number;
  y: number;
  interfaces: Record<string, NetworkInterface>;
  defaultGateway: string | null;
  cli: { mode: CliMode; selectedInterface: string | null };
}

export interface LinkEndpoint {
  deviceId: string;
  interfaceId: string;
}

export interface Link {
  id: string;
  a: LinkEndpoint;
  b: LinkEndpoint;
}

export interface LabSession {
  id: string;
  devices: Device[];
  links: Link[];
  createdAt: number;
  touchedAt: number;
}

export interface PublicInterface extends NetworkInterface {
  linkUp: boolean;
}

export interface PublicDevice extends Omit<Device, 'interfaces' | 'cli'> {
  interfaces: Record<string, PublicInterface>;
}

export interface PublicState {
  id: string;
  devices: PublicDevice[];
  links: Array<Link & { up: boolean }>;
}

