import { useMemo, useState } from 'react';
import type { Device, Endpoint, LabState } from '../types';

export function ConnectModal({ state, source, target, onConnect, onClose }: { state: LabState; source: Device; target: Device; onConnect: (a: Endpoint, b: Endpoint) => Promise<void>; onClose: () => void }) {
  const occupied = useMemo(() => new Set(state.links.flatMap((link) => [`${link.a.deviceId}:${link.a.interfaceId}`, `${link.b.deviceId}:${link.b.interfaceId}`])), [state.links]);
  const free = (device: Device) => Object.values(device.interfaces).filter((iface) => !occupied.has(`${device.id}:${iface.id}`));
  const sourcePorts = free(source); const targetPorts = free(target);
  const [sourcePort, setSourcePort] = useState(sourcePorts[0]?.id ?? '');
  const [targetPort, setTargetPort] = useState(targetPorts[0]?.id ?? '');
  const [error, setError] = useState('');
  async function connect() {
    if (!sourcePort || !targetPort) { setError('Both devices need a free interface.'); return; }
    try { await onConnect({ deviceId: source.id, interfaceId: sourcePort }, { deviceId: target.id, interfaceId: targetPort }); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Connection failed'); }
  }
  return <div className="modal-backdrop" onMouseDown={onClose}><section className="connect-dialog" onMouseDown={(event) => event.stopPropagation()}>
    <header><span>Connect copper cable</span><button onClick={onClose}>×</button></header>
    <div className="cable-end"><strong>{source.name}</strong><select value={sourcePort} onChange={(event) => setSourcePort(event.target.value)}>{sourcePorts.map((iface) => <option value={iface.id} key={iface.id}>{iface.name}</option>)}</select></div>
    <div className="cable-glyph">↔</div>
    <div className="cable-end"><strong>{target.name}</strong><select value={targetPort} onChange={(event) => setTargetPort(event.target.value)}>{targetPorts.map((iface) => <option value={iface.id} key={iface.id}>{iface.name}</option>)}</select></div>
    {error && <p className="error-text">{error}</p>}
    <footer><button onClick={onClose}>Cancel</button><button className="primary" onClick={connect}>Connect</button></footer>
  </section></div>;
}

