import { useCallback, useEffect, useMemo, useRef, useState, type DragEvent } from 'react';
import { Background, BackgroundVariant, Controls, MiniMap, ReactFlow, ReactFlowProvider, useReactFlow, type Edge, type Node } from '@xyflow/react';
import { api } from './api/client';
import { ConnectModal } from './components/ConnectModal';
import { DeviceIcon } from './components/DeviceIcon';
import { DeviceModal } from './components/DeviceModal';
import { InstructionsPanel } from './components/InstructionsPanel';
import { NetworkNode, type NetworkNodeData } from './components/NetworkNode';
import { NetworkEdge, type NetworkEdgeData } from './components/NetworkEdge';
import { ToolbarIcon } from './components/ToolbarIcon';
import type { Device, DeviceType, Endpoint, Instructions, LabState } from './types';

const nodeTypes = { networkDevice: NetworkNode };
const edgeTypes = { networkCable: NetworkEdge };

function shortInterfaceName(name: string): string {
  return name.replace(/^FastEthernet/i, 'FE').replace(/^GigabitEthernet/i, 'G');
}

function Workspace() {
  const [state, setState] = useState<LabState | null>(null);
  const [instructions, setInstructions] = useState<Instructions | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [selectedLink, setSelectedLink] = useState<string | null>(null);
  const [openDevice, setOpenDevice] = useState<string | null>(null);
  const [terminalHistory, setTerminalHistory] = useState<Record<string, string>>({});
  const [cableMode, setCableMode] = useState(false);
  const [cableSource, setCableSource] = useState<string | null>(null);
  const [connectPair, setConnectPair] = useState<[string, string] | null>(null);
  const [instructionsOpen, setInstructionsOpen] = useState(true);
  const [welcome, setWelcome] = useState(true);
  const [error, setError] = useState('');
  const workspaceRef = useRef<HTMLElement>(null);
  const placementCursor = useRef(0);
  const { screenToFlowPosition, fitView } = useReactFlow();

  useEffect(() => {
    async function bootstrap() {
      try {
        setInstructions(await api.instructions());
        const stored = sessionStorage.getItem('netlab-session');
        let next: LabState;
        if (stored) { try { next = await api.state(stored); } catch { next = await api.createSession(); } }
        else next = await api.createSession();
        sessionStorage.setItem('netlab-session', next.id);
        placementCursor.current = next.devices.length;
        setState(next);
      } catch (reason) { setError(reason instanceof Error ? reason.message : 'Cannot start the lab'); }
    }
    void bootstrap();
  }, []);

  const updateState = useCallback((next: LabState) => { setState(next); setError(''); }, []);
  const run = useCallback(async (operation: () => Promise<LabState>) => {
    try { updateState(await operation()); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Operation failed'); }
  }, [updateState]);

  const nodes = useMemo<Node<NetworkNodeData>[]>(() => state?.devices.map((device) => {
    const deviceLinks = state.links.filter((link) => link.a.deviceId === device.id || link.b.deviceId === device.id);
    return { id: device.id, type: 'networkDevice', position: { x: device.x, y: device.y }, selected: selectedDevice === device.id,
      data: { name: device.name, deviceType: device.type, selectedForCable: cableSource === device.id, allLinksUp: deviceLinks.length > 0 && deviceLinks.every((link) => link.up) } };
  }) ?? [], [state, selectedDevice, cableSource]);

  const edges = useMemo<Edge<NetworkEdgeData>[]>(() => state?.links.map((link) => {
    const a = state.devices.find((device) => device.id === link.a.deviceId);
    const b = state.devices.find((device) => device.id === link.b.deviceId);
    const aName = a?.interfaces[link.a.interfaceId]?.name ?? link.a.interfaceId;
    const bName = b?.interfaces[link.b.interfaceId]?.name ?? link.b.interfaceId;
    return { id: link.id, type: 'networkCable', source: link.a.deviceId, target: link.b.deviceId, selected: selectedLink === link.id,
      data: { sourcePort: shortInterfaceName(aName), sourcePortFull: aName, targetPort: shortInterfaceName(bName), targetPortFull: bName, up: link.up },
      style: { stroke: link.up ? '#25a848' : '#d33a32', strokeWidth: selectedLink === link.id ? 4 : 3, filter: selectedLink === link.id ? 'drop-shadow(0 0 2px #2384b4)' : undefined } };
  }) ?? [], [state, selectedLink]);

  const addDevice = useCallback((type: DeviceType, position?: { x: number; y: number }) => {
    if (!state) return;
    let target = position;
    if (!target) {
      const rect = workspaceRef.current?.getBoundingClientRect();
      if (!rect) return;
      const drawerWidth = instructionsOpen ? Math.min(390, rect.width * .85) : 0;
      const visibleWidth = Math.max(280, rect.width - drawerWidth);
      const spacingX = 125;
      const spacingY = 115;
      const columns = Math.max(1, Math.floor((visibleWidth - 100) / spacingX));
      const slot = placementCursor.current;
      target = screenToFlowPosition({
        x: rect.left + 75 + (slot % columns) * spacingX,
        y: rect.top + 85 + Math.floor(slot / columns) * spacingY,
      });
    }
    placementCursor.current += 1;
    void run(() => api.addDevice(state.id, { type, ...target }));
  }, [instructionsOpen, run, screenToFlowPosition, state]);

  function chooseNode(id: string) {
    setSelectedLink(null);
    if (!cableMode) { setSelectedDevice(id); return; }
    if (!cableSource) { setCableSource(id); return; }
    if (cableSource !== id) setConnectPair([cableSource, id]);
  }

  const removeSelection = useCallback(() => {
    if (!state) return;
    if (selectedLink) void run(() => api.deleteLink(state.id, selectedLink)).then(() => setSelectedLink(null));
    else if (selectedDevice) void run(() => api.deleteDevice(state.id, selectedDevice)).then(() => {
      sessionStorage.removeItem(`netlab-terminal:${state.id}:${selectedDevice}`);
      setTerminalHistory((history) => { const next = { ...history }; delete next[selectedDevice]; return next; });
      setSelectedDevice(null);
    });
  }, [run, selectedDevice, selectedLink, state]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => { if ((event.key === 'Delete' || event.key === 'Backspace') && !(event.target instanceof HTMLInputElement)) removeSelection(); };
    window.addEventListener('keydown', handler); return () => window.removeEventListener('keydown', handler);
  }, [removeSelection]);

  async function connect(a: Endpoint, b: Endpoint) {
    if (!state) return;
    updateState(await api.addLink(state.id, a, b)); setConnectPair(null); setCableSource(null); setCableMode(false);
  }

  function reset() {
    if (!state || !window.confirm('Reset current lab?')) return;
    for (const device of state.devices) sessionStorage.removeItem(`netlab-terminal:${state.id}:${device.id}`);
    setTerminalHistory({});
    placementCursor.current = 0;
    void run(() => api.reset(state.id)).then(() => { setSelectedDevice(null); setSelectedLink(null); setOpenDevice(null); setCableSource(null); setCableMode(false); setTimeout(() => fitView(), 50); });
  }

  function drop(event: DragEvent) {
    event.preventDefault(); const type = event.dataTransfer.getData('application/netlab') as DeviceType;
    if (['pc', 'switch', 'router'].includes(type)) addDevice(type, screenToFlowPosition({ x: event.clientX, y: event.clientY }));
  }

  const opened = state?.devices.find((device) => device.id === openDevice);
  const openedTranscript = opened && state ? terminalHistory[opened.id] ?? sessionStorage.getItem(`netlab-terminal:${state.id}:${opened.id}`) ?? '' : '';
  const pairDevices = connectPair ? connectPair.map((id) => state?.devices.find((device) => device.id === id)).filter(Boolean) as Device[] : [];
  const counts = (type: DeviceType) => state?.devices.filter((device) => device.type === type).length ?? 0;

  return <div className="app-shell">
    <header className="application-bar"><div className="brand-mark"><span>NL</span></div><strong>Network Lab Simulator</strong><div className="header-actions"><button onClick={() => setInstructionsOpen(!instructionsOpen)}><ToolbarIcon name="note"/>Instructions</button><button className="header-reset" onClick={reset}>↻ Reset Lab</button></div></header>
    <main className="main-area">
      <div className="workspace-column">
      <section ref={workspaceRef} className="workspace" onDrop={drop} onDragOver={(event) => event.preventDefault()}>
        {!state && <div className="loading">Starting network simulator…</div>}
        {state && <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} minZoom={.25} maxZoom={2} fitView
          onNodeClick={(_event, node) => chooseNode(node.id)} onNodeDoubleClick={(_event, node) => { if (!cableMode) setOpenDevice(node.id); }}
          onNodeDragStop={(_event, node) => void run(() => api.moveDevice(state.id, node.id, node.position.x, node.position.y))}
          onEdgeClick={(_event, edge) => { setSelectedLink(edge.id); setSelectedDevice(null); }}
          onPaneClick={() => { if (!cableMode) { setSelectedDevice(null); setSelectedLink(null); } }}>
          <Background color="#b5b9bd" gap={20} size={1} variant={BackgroundVariant.Dots}/><Controls position="top-left"/><MiniMap position="bottom-right" pannable zoomable nodeColor={(node) => node.data.deviceType === 'router' ? '#6798b0' : node.data.deviceType === 'switch' ? '#87949b' : '#a9cddd'}/>
        </ReactFlow>}
        {cableMode && <div className="mode-banner">{cableSource ? 'Select the second device' : 'Select the first device'} <button onClick={() => { setCableMode(false); setCableSource(null); }}>Cancel</button></div>}
        {(selectedDevice || selectedLink) && <button className="delete-selection" title="Delete selected object" onClick={removeSelection}><ToolbarIcon name="delete"/>Delete selected</button>}
      </section>
      </div>
      <InstructionsPanel instructions={instructions} open={instructionsOpen} onToggle={() => setInstructionsOpen(!instructionsOpen)}/>
    </main>
    <section className="device-palette">
      <div className="device-selection"><div className="selection-header"><strong>Devices &amp; Connections</strong><span>Drag a device to the workspace or choose a cable</span></div><div className="device-list">
        {(['pc', 'switch', 'router'] as DeviceType[]).map((type) => { const max = type === 'router' ? 1 : 2; const disabled = counts(type) >= max; return <button key={type} disabled={disabled} draggable={!disabled}
          onDragStart={(event) => { event.dataTransfer.setData('application/netlab', type); event.dataTransfer.effectAllowed = 'copy'; }} onClick={() => addDevice(type)}>
          <DeviceIcon type={type} size={48}/><span>{type === 'pc' ? 'PC-PT' : type === 'switch' ? 'Switch-PT' : 'Router-PT'}</span><small>{counts(type)} of {max}</small></button>; })}
        <button className={cableMode ? 'cable-device selected' : 'cable-device'} onClick={() => { setCableMode(!cableMode); setCableSource(null); }}><ToolbarIcon name="cable"/><span>Copper Straight-Through</span><small>Auto-Connect</small></button>
      </div></div>
    </section>
    <footer className="status-bar"><span><i className={state ? 'online' : ''}/> {state ? 'Ready' : 'Connecting to simulation engine…'}</span><span>Select a device type to drag and drop into the workspace.</span><span>{state?.devices.length ?? 0} Devices &nbsp; {state?.links.length ?? 0} Connections &nbsp; Session: {state?.id.slice(0, 8) ?? '—'}</span></footer>
    {error && <div className="error-toast">⚠ {error}<button onClick={() => setError('')}>×</button></div>}
    {opened && state && <DeviceModal sessionId={state.id} device={opened} terminalTranscript={openedTranscript} onTerminalTranscript={(transcript) => {
      setTerminalHistory((history) => ({ ...history, [opened.id]: transcript }));
      sessionStorage.setItem(`netlab-terminal:${state.id}:${opened.id}`, transcript);
    }} onState={updateState} onClose={() => setOpenDevice(null)}/>} 
    {pairDevices.length === 2 && state && <ConnectModal state={state} source={pairDevices[0]!} target={pairDevices[1]!} onConnect={connect} onClose={() => { setConnectPair(null); setCableSource(null); }}/>} 
    {welcome && <div className="modal-backdrop"><section className="welcome-dialog"><div className="welcome-icon">⌘</div><h1>Network Connectivity Challenge</h1><p>Your task is to build and configure a network that allows <strong>PC1</strong> to communicate with <strong>PC2</strong>.</p><p>Use the addressing table in the Instructions panel. Double-click a device to configure it.</p><p className="welcome-note">A successful end-to-end connection completes the challenge.</p><button className="primary" onClick={() => setWelcome(false)}>Start building</button></section></div>}
  </div>;
}

export function App() { return <ReactFlowProvider><Workspace /></ReactFlowProvider>; }
