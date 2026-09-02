export const challenge = {
  pc1: { ip: '192.168.10.10', mask: '255.255.255.0', gateway: '192.168.10.1' },
  router: {
    'g0/0': { ip: '192.168.10.1', mask: '255.255.255.0' },
    'g0/1': { ip: '192.168.20.1', mask: '255.255.255.0' },
  },
  pc2: { ip: '192.168.20.10', mask: '255.255.255.0', gateway: '192.168.20.1' },
} as const;

export const publicInstructions = {
  title: 'Network Challenge',
  objective: 'Build the topology and establish connectivity between PC1 and PC2.',
  addressing: [
    { device: 'PC1', interface: 'FastEthernet0', ip: challenge.pc1.ip, mask: challenge.pc1.mask, gateway: challenge.pc1.gateway },
    { device: 'R1', interface: 'G0/0', ip: challenge.router['g0/0'].ip, mask: challenge.router['g0/0'].mask, gateway: 'N/A' },
    { device: 'R1', interface: 'G0/1', ip: challenge.router['g0/1'].ip, mask: challenge.router['g0/1'].mask, gateway: 'N/A' },
    { device: 'PC2', interface: 'FastEthernet0', ip: challenge.pc2.ip, mask: challenge.pc2.mask, gateway: challenge.pc2.gateway },
  ],
};

