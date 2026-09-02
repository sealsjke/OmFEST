import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { DeviceType } from '../types';
import { DeviceIcon } from './DeviceIcon';

export type NetworkNodeData = { name: string; deviceType: DeviceType; selectedForCable?: boolean; allLinksUp: boolean };

export function NetworkNode({ data, selected }: NodeProps) {
  const value = data as NetworkNodeData;
  return (
    <div className={`network-node ${selected ? 'selected' : ''} ${value.selectedForCable ? 'cable-source' : ''}`}>
      <Handle type="target" position={Position.Left} className="flow-handle" />
      <DeviceIcon type={value.deviceType} />
      <div className="node-label">{value.name}</div>
      <span className={`node-led ${value.allLinksUp ? 'up' : 'down'}`} title={value.allLinksUp ? 'Connected' : 'Disconnected'} />
      <Handle type="source" position={Position.Right} className="flow-handle" />
    </div>
  );
}

