import { useEffect, useRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { api } from '../api/client';
import type { Device, LabState } from '../types';

export function TerminalPanel({ sessionId, device, initialTranscript, onTranscriptChange, onState, onExit }: {
  sessionId: string;
  device: Device;
  initialTranscript: string;
  onTranscriptChange: (transcript: string) => void;
  onState: (state: LabState) => void;
  onExit: () => void;
}) {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!host.current) return;
    const terminal = new Terminal({ cursorBlink: true, convertEol: true, fontFamily: 'Consolas, "Liberation Mono", monospace', fontSize: 14, theme: { background: '#071009', foreground: '#e4ece5', cursor: '#f7f7f7', selectionBackground: '#395846' }, scrollback: 1500 });
    const fit = new FitAddon();
    terminal.loadAddon(fit);
    terminal.open(host.current);
    fit.fit();
    const initialPrompt = device.type === 'pc' ? 'C:\\>' : device.type === 'router' ? 'Router>' : 'Switch>';
    const banner = device.type === 'pc' ? 'PC Command Line 1.0' : `${device.type === 'router' ? 'Router' : 'Switch'} Network Operating System`;
    let transcript = initialTranscript || `${banner}\r\n\r\n${initialPrompt}`;
    const persist = () => onTranscriptChange(transcript.slice(-100_000));
    terminal.write(transcript);
    let line = '';
    let busy = false;
    const input = terminal.onData(async (data) => {
      if (busy) return;
      if (data === '\r') {
        busy = true;
        terminal.write('\r\n');
        transcript += `${line}\r\n`;
        try {
          const result = await api.command(sessionId, device.id, line);
          if (result.clear) {
            terminal.clear();
            transcript = '';
          } else if (result.output) {
            terminal.write(`${result.output}\r\n`);
            transcript += `${result.output}\r\n`;
          }
          onState(result.state);
          line = '';
          if (result.exited) {
            transcript += result.prompt;
            persist();
            onExit();
          } else {
            terminal.write(result.prompt);
            transcript += result.prompt;
            persist();
          }
        } catch (error) {
          const message = `Error: ${error instanceof Error ? error.message : 'request failed'}`;
          terminal.writeln(message);
          terminal.write(initialPrompt);
          transcript += `${message}\r\n${initialPrompt}`;
          persist();
          line = '';
        } finally { busy = false; }
      } else if (data === '\u007f') {
        if (line.length) { line = line.slice(0, -1); terminal.write('\b \b'); }
      } else if (data >= ' ' && data !== '\u007f' && line.length < 200) {
        line += data; terminal.write(data);
      }
    });
    const observer = new ResizeObserver(() => fit.fit());
    observer.observe(host.current);
    terminal.focus();
    return () => { persist(); observer.disconnect(); input.dispose(); terminal.dispose(); };
    // The terminal intentionally stays mounted for the lifetime of this device modal.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, device.id]);

  return <div ref={host} className="terminal-host" />;
}
