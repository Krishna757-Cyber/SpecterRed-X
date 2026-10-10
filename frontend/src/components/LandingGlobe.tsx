// Procedural 3D network globe for the landing hero: a wireframe sphere with
// red (adversarial) and blue (defensive) activity arcs. Purely decorative; it
// does not claim to be live simulation data.
import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

function latLngToVec3(lat: number, lng: number, r: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180)
  const theta = (lng + 180) * (Math.PI / 180)
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta),
  )
}

function Arc({ color, seed }: { color: string; seed: number }) {
  const curve = useMemo(() => {
    const rnd = (n: number) => ((Math.sin(seed * 999 + n) + 1) / 2) * 2 - 1
    const start = latLngToVec3(rnd(1) * 80, rnd(2) * 180, 2)
    const end = latLngToVec3(rnd(3) * 80, rnd(4) * 180, 2)
    const mid = start.clone().add(end).multiplyScalar(0.5).normalize().multiplyScalar(2.9)
    return new THREE.QuadraticBezierCurve3(start, mid, end)
  }, [seed])

  const points = useMemo(() => curve.getPoints(40), [curve])
  const geo = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points])
  const dotRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (!dotRef.current) return
    const t = (Math.sin(state.clock.getElapsedTime() * 0.6 + seed) + 1) / 2
    dotRef.current.position.copy(curve.getPoint(t))
  })

  return (
    <group>
      <primitive object={new THREE.Line(geo, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.5 }))} />
      <mesh ref={dotRef}>
        <sphereGeometry args={[0.04, 8, 8]} />
        <meshBasicMaterial color={color} />
      </mesh>
    </group>
  )
}

function Globe({ reducedMotion }: { reducedMotion: boolean }) {
  const group = useRef<THREE.Group>(null)
  useFrame((state) => {
    if (group.current && !reducedMotion) group.current.rotation.y = state.clock.getElapsedTime() * 0.12
  })
  const nodes = useMemo(() => {
    const pts: THREE.Vector3[] = []
    for (let i = 0; i < 60; i++) {
      pts.push(latLngToVec3((Math.random() - 0.5) * 160, (Math.random() - 0.5) * 360, 2))
    }
    return pts
  }, [])

  return (
    <group ref={group}>
      <mesh>
        <sphereGeometry args={[2, 24, 24]} />
        <meshBasicMaterial color="#0D1220" transparent opacity={0.55} />
      </mesh>
      <mesh>
        <sphereGeometry args={[2.002, 16, 16]} />
        <meshBasicMaterial color="#1b2740" wireframe transparent opacity={0.35} />
      </mesh>
      {nodes.map((p, i) => (
        <mesh key={i} position={p}>
          <sphereGeometry args={[0.02, 6, 6]} />
          <meshBasicMaterial color={i % 3 === 0 ? '#9B7CFF' : '#00D9FF'} />
        </mesh>
      ))}
      {Array.from({ length: 6 }).map((_, i) => (
        <Arc key={`r${i}`} color="#FF304F" seed={i + 1} />
      ))}
      {Array.from({ length: 6 }).map((_, i) => (
        <Arc key={`b${i}`} color="#278BFF" seed={i + 20} />
      ))}
    </group>
  )
}

export function LandingGlobe({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <Canvas camera={{ position: [0, 0, 6], fov: 45 }} dpr={[1, 1.75]} gl={{ antialias: true }}>
      <ambientLight intensity={0.6} />
      <pointLight position={[5, 5, 5]} intensity={30} color="#7047FF" />
      <Globe reducedMotion={reducedMotion} />
    </Canvas>
  )
}
