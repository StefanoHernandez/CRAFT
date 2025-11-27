import React, { useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Vector3, QuadraticBezierCurve3, BufferGeometry } from 'three';
import { useNexusStore } from '../../stores/nexusStore';
import * as THREE from 'three';

const NODE_POSITIONS: Record<string, [number, number, number]> = {
    agent: [0, 0, 0],
    provider: [0, 2, -2],
    tools: [2, 1, 1],
    memory: [-2, 1, 1],
};

export function DataFlow() {
    const packets = useNexusStore((state) => state.packets);
    const updatePackets = useNexusStore((state) => state.updatePackets);

    useFrame((_state, delta) => {
        updatePackets(delta * 1.5); // Speed multiplier
    });

    return (
        <group>
            {packets.map((packet) => (
                <Packet key={packet.id} packet={packet} />
            ))}
            <Connections />
        </group>
    );
}

function Packet({ packet }: { packet: any }) {
    const start = new Vector3(...NODE_POSITIONS[packet.from]);
    const end = new Vector3(...NODE_POSITIONS[packet.to]);

    // Control point for curve (midpoint + offset)
    const mid = start.clone().add(end).multiplyScalar(0.5);
    mid.y += 1; // Arch effect

    const curve = useMemo(() => new QuadraticBezierCurve3(start, mid, end), [start, end]);
    const point = curve.getPoint(packet.progress);

    return (
        <mesh position={point}>
            <sphereGeometry args={[0.08, 8, 8]} />
            <meshBasicMaterial color={packet.color} />
        </mesh>
    );
}

function Connections() {
    const start = new Vector3(...NODE_POSITIONS['agent']);

    return (
        <group>
            {['provider', 'tools', 'memory'].map((target) => {
                const end = new Vector3(...NODE_POSITIONS[target]);
                const mid = start.clone().add(end).multiplyScalar(0.5);
                mid.y += 1;

                const curve = new QuadraticBezierCurve3(start, mid, end);
                const points = curve.getPoints(20);
                const geometry = new BufferGeometry().setFromPoints(points);

                return (
                    <primitive
                        key={target}
                        object={new (THREE as any).Line(
                            geometry,
                            new (THREE as any).LineBasicMaterial({ color: "#334155", transparent: true, opacity: 0.3 })
                        )}
                    />
                );
            })}
        </group>
    );
}
