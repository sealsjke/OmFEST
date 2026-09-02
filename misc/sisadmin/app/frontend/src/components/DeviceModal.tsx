import { useState } from 'react';
import { api } from '../api/client';
import type { Device, LabState } from '../types';
import { DeviceIcon } from './DeviceIcon';
import { TerminalPanel } from './TerminalPanel';

export function DeviceModal({ sessionId, device, terminalTranscript, onTerminalTranscript, onState, onClose }: {
  sessionId: string;
  device: Device;
  terminalTranscript: string;
  onTerminalTranscript: (transcript: string) => void;
  onState: (state: LabState) => void;
  onClose: () => void;
}) {
  const [tab, setTab] = useState<'config' | 'terminal'>(device.type === 'pc' ? 'config' : 'terminal');
  const iface = device.interfaces.fa0;
  const [ip, setIp] = useState(iface?.ip ?? '');
  const [mask, setMask] = useState(iface?.mask ?? '255.255.255.0');
  const [gateway, setGateway] = useState(device.defaultGateway ?? '');
  const [message, setMessage] = useState('');

  async function save() {
    try { onState(await api.configurePc(sessionId, device.id, { ip, mask, gateway })); setMessage('Configuration saved.'); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Could not save configuration'); }
  }

  return <div className="modal-backdrop" onMouseDown={onClose}>
    <section className="device-window" onMouseDown={(event) => event.stopPropagation()}>
      <header className="window-titlebar"><div className="title-device"><DeviceIcon type={device.type} size={28}/><span>{device.name}</span></div><button onClick={onClose} aria-label="Close">×</button></header>
      <nav className="window-tabs">
        {device.type === 'pc' && <button className={tab === 'config' ? 'active' : ''} onClick={() => setTab('config')}>Desktop · IP Configuration</button>}
        <button className={tab === 'terminal' ? 'active' : ''} onClick={() => setTab('terminal')}>{device.type === 'pc' ? 'Command Prompt' : 'CLI'}</button>
      </nav>
      <div className="window-content">
        {tab === 'config' && device.type === 'pc' ? <div className="ip-config">
          <h3>IP Configuration</h3><p>Configure the FastEthernet0 adapter.</p>
          <label>IP Address<input value={ip} onChange={(event) => setIp(event.target.value)} placeholder="0.0.0.0" /></label>
          <label>Subnet Mask<input value={mask} onChange={(event) => setMask(event.target.value)} placeholder="255.255.255.0" /></label>
          <label>Default Gateway<input value={gateway} onChange={(event) => setGateway(event.target.value)} placeholder="0.0.0.0" /></label>
          <div className="form-footer"><span className={message.includes('saved') ? 'success-text' : 'error-text'}>{message}</span><button className="primary" onClick={save}>Save configuration</button></div>
        </div> : <div className="terminal-wrapper"><TerminalPanel sessionId={sessionId} device={device} initialTranscript={terminalTranscript} onTranscriptChange={onTerminalTranscript} onState={onState} onExit={onClose}/></div>}
      </div>
    </section>
  </div>;
}
