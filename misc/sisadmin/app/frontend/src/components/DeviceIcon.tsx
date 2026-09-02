import type { DeviceType } from '../types';

export function DeviceIcon({ type, size = 62 }: { type: DeviceType; size?: number }) {
  if (type === 'pc') return (
    <svg className="device-svg" width={size} height={size} viewBox="0 0 72 72" aria-hidden="true">
      <defs><linearGradient id="screen" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#c9edff"/><stop offset="1" stopColor="#4389b2"/></linearGradient></defs>
      <rect x="8" y="8" width="56" height="39" rx="3" fill="#dadde1" stroke="#3f4850" strokeWidth="2"/>
      <rect x="12" y="12" width="48" height="29" fill="url(#screen)" stroke="#6c757d"/>
      <path d="M31 47v8h-9v5h28v-5h-9v-8" fill="#aeb4ba" stroke="#3f4850" strokeWidth="2"/>
      <circle cx="57" cy="44" r="1.5" fill="#42a647"/>
    </svg>
  );
  if (type === 'switch') return (
    <svg className="device-svg" width={size} height={size} viewBox="0 0 80 64" aria-hidden="true">
      <defs><linearGradient id="switchBody" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#e5e9ec"/><stop offset="1" stopColor="#8d979f"/></linearGradient></defs>
      <path d="M9 20h62l5 7v24H4V27z" fill="url(#switchBody)" stroke="#3b444b" strokeWidth="2"/>
      <path d="M9 20l-5 7h72l-5-7z" fill="#c9d0d5"/>
      {[0,1,2,3,4,5,6,7].map((n) => <g key={n}><rect x={10+n*8} y="34" width="5" height="7" rx=".5" fill="#202a30"/><circle cx={12.5+n*8} cy="46" r="1.4" fill={n < 2 ? '#51c257' : '#6b747b'}/></g>)}
    </svg>
  );
  return (
    <svg className="device-svg" width={size} height={size} viewBox="0 0 88 64" aria-hidden="true">
      <defs>
        <linearGradient id="routerTop" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#eef2f4"/><stop offset="1" stopColor="#aab4ba"/></linearGradient>
        <linearGradient id="routerFront" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#7f8b92"/><stop offset="1" stopColor="#4c5960"/></linearGradient>
      </defs>
      <ellipse cx="44" cy="54" rx="35" ry="4" fill="#263238" opacity=".18"/>
      <path d="M8 20 18 9h58l7 11z" fill="url(#routerTop)" stroke="#37454d" strokeWidth="1.7" strokeLinejoin="round"/>
      <path d="M8 20h75v29H8z" fill="url(#routerFront)" stroke="#37454d" strokeWidth="1.7"/>
      <path d="M13 25h65v18H13z" fill="#d8dde0" stroke="#303c43" strokeWidth="1.2"/>
      <g fill="#48545b">
        <path d="M23 13h34v1.4H23zM20 16h40v1.4H20z" opacity=".55"/>
        <rect x="18" y="29" width="18" height="2" rx="1"/><rect x="18" y="33" width="18" height="2" rx="1"/><rect x="18" y="37" width="18" height="2" rx="1"/>
      </g>
      <g stroke="#202a2f" strokeWidth="1">
        <path d="M46 28h12v11H46z" fill="#27343a"/><path d="M62 28h12v11H62z" fill="#27343a"/>
        <path d="M49 31h6v5h-6zM65 31h6v5h-6z" fill="#11191d"/>
        <path d="M50 29v2M53 29v2M66 29v2M69 29v2" stroke="#c7d0d4" strokeWidth=".7"/>
      </g>
      <circle cx="15" cy="29" r="1.5" fill="#53d05d"/><circle cx="15" cy="34" r="1.5" fill="#f3c844"/><circle cx="15" cy="39" r="1.5" fill="#6e7a80"/>
      <path d="M13 49v4h8l2-4M78 49v4h-8l-2-4" fill="#39464c"/>
      <text x="44" y="47" textAnchor="middle" fill="#eef3f5" fontSize="3.7" fontFamily="Arial, sans-serif" letterSpacing="1">NETWORK ROUTER</text>
    </svg>
  );
}
