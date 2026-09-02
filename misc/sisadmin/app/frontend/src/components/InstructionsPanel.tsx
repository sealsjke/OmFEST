import type { Instructions } from '../types';

export function InstructionsPanel({ instructions, open, onToggle }: { instructions: Instructions | null; open: boolean; onToggle: () => void }) {
  return <aside className={`instructions ${open ? 'open' : ''}`}>
    <button className="instructions-toggle" onClick={onToggle}>{open ? '›' : '‹'}</button>
    {open && <div className="instructions-content"><h2>{instructions?.title ?? 'Network Challenge'}</h2><p>Configure the network according to the addressing table.</p>
      <div className="address-table-wrap"><table><thead><tr><th>Device</th><th>Interface</th><th>IP Address</th><th>Subnet Mask</th><th>Gateway</th></tr></thead>
        <tbody>{instructions?.addressing.map((row) => <tr key={`${row.device}-${row.interface}`}><td>{row.device}</td><td>{row.interface}</td><td>{row.ip}</td><td>{row.mask}</td><td>{row.gateway}</td></tr>)}</tbody></table></div>
      <h3>Objective</h3><p>{instructions?.objective}</p><div className="hint"><span>i</span> Router Ethernet interfaces are administratively down until you enter <code>no shutdown</code>.</div>
    </div>}
  </aside>;
}

