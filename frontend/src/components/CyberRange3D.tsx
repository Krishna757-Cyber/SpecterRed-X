// Procedural 3D cyber-range scene (React Three Fiber). Low-poly, instanced where
// useful, shared materials, bounded orbit. Renders a scenario's assets as nodes,
// network edges, translucent zones, and an animated packet tied to the currently
// selected persisted event. No external model files.
import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Grid, Line, OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import type { Asset, SimEvent } from '@/types'
import type { Quality } from '@/lib/quality'

const KIND_COLOR: Record<Asset['kind'], string> = {
  service: '#00D9FF',
  identity: '#9B7CFF',
  data: '#278BFF',
  control: '#29D391',
}

const OUTCOME_COLOR = {
  succeeded: '#FF304F',
  detected: '#278BFF',
  prevented: '#29D391',
} as const

function AssetNode({
  asset,
  selected,
  active,
  activeColor,
  onSelect,
  reducedMotion,
}: {
  asset: Asset
  selected: boolean
  active: boolean
  activeColor: string
  onSelect: (id: string) => void
  reducedMotion: boolean
}) {
  const ref = useRef<THREE.Mesh>(null)
  const ringRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (reducedMotion) return
    if (active && ringRef.current) {
      const t = state.clock.getElapsedTime()
      const s = 1 + Math.sin(t * 3) * 0.12
      ringRef.current.scale.setScalar(s)
    }
    if (ref.current && active) {
      ref.current.rotation.y += 0.01
    }
  })

  const color = active ? activeColor : KIND_COLOR[asset.kind]
  const geo = asset.kind === 'identity' ? 'ico' : asset.kind === 'data' ? 'box' : asset.kind === 'control' ? 'oct' : 'cyl'

  return (
    <group position={asset.pos}>
      <mesh
        ref={ref}
        onClick={(e) => {
          e.stopPropagation()
          onSelect(asset.id)
        }}
        onPointerOver={(e) => {
          e.stopPropagation()
          document.body.style.cursor = 'pointer'
        }}
        onPointerOut={() => {
          document.body.style.cursor = 'auto'
        }}
      >
        {geo === 'ico' && <icosahedronGeometry args={[0.55, 0]} />}
        {geo === 'box' && <boxGeometry args={[0.9, 0.9, 0.9]} />}
        {geo === 'oct' && <octahedronGeometry args={[0.6, 0]} />}
        {geo === 'cyl' && <cylinderGeometry args={[0.5, 0.5, 0.9, 6]} />}
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={active ? 0.9 : 0.25}
          metalness={0.3}
          roughness={0.4}
          transparent
          opacity={0.92}
        />
      </mesh>

      {/* selection / active ring */}
      {(selected || active) && (
        <mesh ref={ringRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.7, 0]}>
          <ringGeometry args={[0.7, 0.82, 32]} />
          <meshBasicMaterial color={active ? activeColor : '#00D9FF'} transparent opacity={0.8} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* control assets get a protective shield dome */}
      {asset.kind === 'control' && (
        <mesh>
          <sphereGeometry args={[1.0, 16, 12]} />
          <meshBasicMaterial color="#29D391" transparent opacity={0.08} side={THREE.BackSide} />
        </mesh>
      )}
    </group>
  )
}

function Packet({ from, to, color, reducedMotion }: { from: THREE.Vector3; to: THREE.Vector3; color: string; reducedMotion: boolean }) {
  const ref = useRef<THREE.Mesh>(null)
  useFrame((state) => {
    if (!ref.current) return
    const t = reducedMotion ? 0.5 : (Math.sin(state.clock.getElapsedTime() * 1.5) + 1) / 2
    ref.current.position.lerpVectors(from, to, t)
  })
  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.16, 12, 12]} />
      <meshBasicMaterial color={color} />
    </mesh>
  )
}

function SceneContent({
  assets,
  event,
  selectedAsset,
  onSelectAsset,
  quality,
  reducedMotion,
}: {
  assets: Asset[]
  event: SimEvent | null
  selectedAsset: string | null
  onSelectAsset: (id: string) => void
  quality: Quality
  reducedMotion: boolean
}) {
  const posById = useMemo(() => {
    const m = new Map<string, THREE.Vector3>()
    assets.forEach((a) => m.set(a.id, new THREE.Vector3(...a.pos)))
    return m
  }, [assets])

  // Build a stable set of edges (star to SOC + sequential chain) once.
  const edges = useMemo(() => {
    const list: [THREE.Vector3, THREE.Vector3][] = []
    const soc = assets.find((a) => a.kind === 'control')
    for (let i = 0; i < assets.length - 1; i++) {
      list.push([posById.get(assets[i].id)!, posById.get(assets[i + 1].id)!])
    }
    if (soc) {
      assets
        .filter((a) => a.kind !== 'control')
        .forEach((a) => list.push([posById.get(a.id)!, posById.get(soc.id)!]))
    }
    return list
  }, [assets, posById])

  const activeAssets = new Set(event?.affects_assets ?? [])
  const activeColor = event ? OUTCOME_COLOR[event.outcome] : '#00D9FF'

  // Packet travels between the two assets this event affects.
  const packetPair = useMemo(() => {
    if (!event || event.affects_assets.length < 1) return null
    const a = posById.get(event.affects_assets[0])
    const b = posById.get(event.affects_assets[event.affects_assets.length - 1]) ?? a
    return a && b ? ([a, b] as const) : null
  }, [event, posById])

  const particleCount = quality === 'high' ? 240 : 60

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[8, 10, 8]} intensity={60} color="#7047FF" />
      <pointLight position={[-8, 6, -6]} intensity={40} color="#00D9FF" />
      <fog attach="fog" args={['#080B12', 14, 34]} />

      <Grid
        args={[40, 40]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#1b2740"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#2a3b5c"
        fadeDistance={32}
        fadeStrength={1.5}
        position={[0, -1.2, 0]}
        infiniteGrid
      />

      {edges.map((e, i) => (
        <Line key={i} points={[e[0], e[1]]} color="#2a3b5c" lineWidth={1} transparent opacity={0.5} />
      ))}

      {assets.map((a) => (
        <AssetNode
          key={a.id}
          asset={a}
          selected={selectedAsset === a.id}
          active={activeAssets.has(a.id)}
          activeColor={activeColor}
          onSelect={onSelectAsset}
          reducedMotion={reducedMotion}
        />
      ))}

      {packetPair && <Packet from={packetPair[0]} to={packetPair[1]} color={activeColor} reducedMotion={reducedMotion} />}

      {quality === 'high' && <Particles count={particleCount} reducedMotion={reducedMotion} />}

      <OrbitControls
        enablePan={false}
        minDistance={8}
        maxDistance={26}
        maxPolarAngle={Math.PI / 2.1}
        autoRotate={!reducedMotion && !event}
        autoRotateSpeed={0.3}
      />
    </>
  )
}

function Particles({ count, reducedMotion }: { count: number; reducedMotion: boolean }) {
  const ref = useRef<THREE.Points>(null)
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 30
      arr[i * 3 + 1] = Math.random() * 10 - 1
      arr[i * 3 + 2] = (Math.random() - 0.5) * 30
    }
    return arr
  }, [count])
  useFrame((state) => {
    if (ref.current && !reducedMotion) {
      ref.current.rotation.y = state.clock.getElapsedTime() * 0.02
    }
  })
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.05} color="#9B7CFF" transparent opacity={0.5} sizeAttenuation />
    </points>
  )
}

export function CyberRange3D({
  assets,
  event,
  selectedAsset,
  onSelectAsset,
  quality,
  reducedMotion,
}: {
  assets: Asset[]
  event: SimEvent | null
  selectedAsset: string | null
  onSelectAsset: (id: string) => void
  quality: Quality
  reducedMotion: boolean
}) {
  return (
    <Canvas
      camera={{ position: [10, 9, 14], fov: 46 }}
      dpr={quality === 'high' ? [1, 1.75] : [1, 1]}
      gl={{ antialias: quality === 'high', powerPreference: 'high-performance' }}
      onCreated={({ scene }) => {
        scene.background = new THREE.Color('#080B12')
      }}
    >
      <SceneContent
        assets={assets}
        event={event}
        selectedAsset={selectedAsset}
        onSelectAsset={onSelectAsset}
        quality={quality}
        reducedMotion={reducedMotion}
      />
    </Canvas>
  )
}
