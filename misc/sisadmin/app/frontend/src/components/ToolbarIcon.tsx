type IconName = 'new' | 'open' | 'save' | 'print' | 'undo' | 'redo' | 'copy' | 'select' | 'note' | 'delete' | 'inspect' | 'fit' | 'cable' | 'cluster' | 'background' | 'message';

export function ToolbarIcon({ name }: { name: IconName }) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  return <svg viewBox="0 0 24 24" aria-hidden="true" {...common}>
    {name === 'new' && <><path d="M5 2.5h10l4 4V21H5z" fill="#fff"/><path d="M15 2.5v5h4M8 14h8M12 10v8"/></>}
    {name === 'open' && <><path d="M3 7h7l2 2h9l-3 10H5z" fill="#f6c64e"/><path d="M4 7V5h7l2 2h5v2"/></>}
    {name === 'save' && <><path d="M4 3h15l2 2v16H4z" fill="#6ca8d0"/><path d="M7 3v7h10V3M8 15h9v6"/></>}
    {name === 'print' && <><path d="M7 3h10v5H7zM6 17H4v-7h16v7h-2"/><path d="M7 14h10v7H7z" fill="#fff"/></>}
    {name === 'undo' && <><path d="M9 7 4 11l5 4"/><path d="M5 11h8c4 0 6 2 6 6"/></>}
    {name === 'redo' && <><path d="m15 7 5 4-5 4"/><path d="M19 11h-8c-4 0-6 2-6 6"/></>}
    {name === 'copy' && <><rect x="8" y="7" width="11" height="13" fill="#fff"/><path d="M5 17H3V4h11v2"/></>}
    {name === 'select' && <path d="m6 3 11 10-6 1 3 6-2 1-3-6-4 4z" fill="#fff"/>}
    {name === 'note' && <><path d="M4 4h16v13H9l-5 4z" fill="#fff6a9"/><path d="M8 8h8M8 12h6"/></>}
    {name === 'delete' && <><path d="M5 6h14M9 6V3h6v3M7 6l1 15h8l1-15"/><path d="M10 10v7M14 10v7" stroke="#b93232"/></>}
    {name === 'inspect' && <><circle cx="10" cy="10" r="6" fill="#bde2f5"/><path d="m14.5 14.5 6 6"/></>}
    {name === 'fit' && <><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/><rect x="8" y="8" width="8" height="8"/></>}
    {name === 'cable' && <>
      <path d="m13.2 1.5-8.5 11h5.1L7.7 22.4 19.4 8.6h-5.7z" fill="#f5c518" stroke="#485158" strokeWidth="1.1"/>
      <path d="M3.4 18.1 6 20.7M18 3.2l2.6 2.6" stroke="#344047" strokeWidth="2.5"/>
      <path d="m1.7 17.4 2.2-2.2 3.7 3.7-2.2 2.2zM16.4 3.1l2.2-2.2 3.7 3.7-2.2 2.2z" fill="#d7a51e" stroke="#3f484e" strokeWidth=".8"/>
      <path d="m2.5 16.6 3.7 3.7M17.2 2.3 20.9 6" stroke="#f6e2a2" strokeWidth=".55"/>
    </>}
    {name === 'cluster' && <><circle cx="6" cy="7" r="3"/><circle cx="18" cy="7" r="3"/><circle cx="12" cy="18" r="3"/><path d="m8 9 3 6M16 9l-3 6"/></>}
    {name === 'background' && <><rect x="3" y="4" width="18" height="16" fill="#d8eef8"/><circle cx="8" cy="9" r="2" fill="#f2ca49"/><path d="m4 18 5-5 3 3 3-4 5 6"/></>}
    {name === 'message' && <><path d="M4 5h16v11H9l-5 4z" fill="#eff7fb"/><path d="M8 9h8M8 12h5"/></>}
  </svg>;
}
