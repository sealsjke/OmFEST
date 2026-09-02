import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from '@xyflow/react';

export interface NetworkEdgeData extends Record<string, unknown> {
  sourcePort: string;
  sourcePortFull: string;
  targetPort: string;
  targetPortFull: string;
  up: boolean;
}

export function NetworkEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style, selected, data }: EdgeProps) {
  const [path] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, curvature: .22 });
  const edgeData = data as NetworkEdgeData | undefined;
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  const length = Math.max(1, Math.hypot(dx, dy));
  const direction = sourceX <= targetX ? -1 : 1;
  const offsetX = (-dy / length) * 13 * direction;
  const offsetY = (dx / length) * 13 * direction;
  const point = (ratio: number) => ({ x: sourceX + dx * ratio + offsetX, y: sourceY + dy * ratio + offsetY });
  const sourceLabel = point(.2);
  const targetLabel = point(.8);

  return <>
    <BaseEdge id={id} path={path} style={style} interactionWidth={18}/>
    <EdgeLabelRenderer>
      <div className={`edge-port-label ${edgeData?.up ? 'up' : 'down'} ${selected ? 'selected' : ''}`} title={edgeData?.sourcePortFull}
        style={{ transform: `translate(-50%, -50%) translate(${sourceLabel.x}px, ${sourceLabel.y}px)` }}>
        <i/>{edgeData?.sourcePort}
      </div>
      <div className={`edge-port-label ${edgeData?.up ? 'up' : 'down'} ${selected ? 'selected' : ''}`} title={edgeData?.targetPortFull}
        style={{ transform: `translate(-50%, -50%) translate(${targetLabel.x}px, ${targetLabel.y}px)` }}>
        <i/>{edgeData?.targetPort}
      </div>
    </EdgeLabelRenderer>
  </>;
}

