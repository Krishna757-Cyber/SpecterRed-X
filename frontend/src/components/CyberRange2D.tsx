// 2D network fallback (React Flow). Used when WebGL is unavailable, the user
// selects Low/2D quality, or the 3D canvas throws. Mirrors the same asset data
// and highlights the assets touched by the currently selected event.
import { useMemo } from 'react'
import ReactFlow, { Background, Controls, type Edge, type Node } from 'reactflow'
import 'reactflow/dist/style.css'
import type { Asset, SimEvent } from '@/types'

const KIND_COLOR: Record<Asset['kind'], string> = {
  service: '#00D9FF',
  identity: '#9B7CFF',
  data: '#278BFF',
  control: '#29D391',
}
const OUTCOME_COLOR = { succeeded: '#FF304F', detected: '#278BFF', prevented: '#29D391' } as const

export function CyberRange2D({
  assets,
  event,
  selectedAsset,
  onSelectAsset,
}: {
  assets: Asset[]
  event: SimEvent | null
  selectedAsset: string | null
  onSelectAsset: (id: string) => void
}) {
  const active = new Set(event?.affects_assets ?? [])
  const activeColor = event ? OUTCOME_COLOR[event.outcome] : '#00D9FF'

  const nodes: Node[] = useMemo(
    () =>
      assets.map((a) => {
        const isActive = active.has(a.id)
        const isSel = selectedAsset === a.id
        return {
          id: a.id,
          position: { x: (a.pos[0] + 7) * 48, y: (a.pos[2] + 6) * 44 },
          data: { label: `${a.label}` },
          style: {
            background: 'rgba(19,26,41,0.92)',
            color: '#F4F7FC',
            border: `2px solid ${isActive ? activeColor : isSel ? '#00D9FF' : KIND_COLOR[a.kind]}`,
            borderRadius: 12,
            padding: '8px 12px',
            fontSize: 12,
            fontWeight: 600,
            width: 150,
            boxShadow: isActive ? `0 0 20px ${activeColor}66` : 'none',
          },
        }
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [assets, selectedAsset, event],
  )

  const edges: Edge[] = useMemo(() => {
    const list: Edge[] = []
    const soc = assets.find((a) => a.kind === 'control')
    for (let i = 0; i < assets.length - 1; i++) {
      list.push({ id: `e${i}`, source: assets[i].id, target: assets[i + 1].id, style: { stroke: '#2a3b5c' } })
    }
    if (soc) {
      assets
        .filter((a) => a.kind !== 'control')
        .forEach((a, i) => list.push({ id: `s${i}`, source: a.id, target: soc.id, animated: false, style: { stroke: '#223049' } }))
    }
    return list
  }, [assets])

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={(_, n) => onSelectAsset(n.id)}
        fitView
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
      >
        <Background color="#1b2740" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}
