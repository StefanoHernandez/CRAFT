import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh, Vector3 } from 'three';
import { Text, Float } from '@react-three/drei';
import { useNexusStore } from '../../stores/nexusStore';

export function AgentCore() {
    const meshRef = useRef<Mesh>(null);
    const glowRef = useRef<Mesh>(null);
    const status = useNexusStore((state) => state.nodes.find((n) => n.id === 'agent')?.status || 'idle');

    useFrame((state) => {
        if (!meshRef.current || !glowRef.current) return;

        // Rotation
        meshRef.current.rotation.x = state.clock.getElapsedTime() * 0.2;
        meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.3;

        // Pulsing based on status
        const speed = status === 'active' ? 5 : 1;
        const scale = 1 + Math.sin(state.clock.getElapsedTime() * speed) * 0.05;
        meshRef.current.scale.setScalar(scale);

        // Glow pulsing
        glowRef.current.scale.setScalar(scale * 1.2);
        glowRef.current.rotation.x = -state.clock.getElapsedTime() * 0.2;
    });

    const getColor = () => {
        switch (status) {
            case 'active': return '#8b5cf6'; // Purple
            case 'success': return '#10b981'; // Green
            case 'error': return '#ef4444'; // Red
            default: return '#3b82f6'; // Blue
        }
    };

    return (
        <group>
            <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
                {/* Core Mesh */}
                <mesh ref={meshRef}>
                    <icosahedronGeometry args={[1, 1]} />
                    <meshStandardMaterial
                        color={getColor()}
                        wireframe
                        emissive={getColor()}
                        emissiveIntensity={0.5}
                    />
                </mesh>

                {/* Inner Glow */}
                <mesh ref={glowRef}>
                    <icosahedronGeometry args={[0.8, 0]} />
                    <meshBasicMaterial
                        color={getColor()}
                        transparent
                        opacity={0.2}
                    />
                </mesh>

                {/* Label */}
                <Text
                    position={[0, -1.5, 0]}
                    fontSize={0.2}
                    color="white"
                    anchorX="center"
                    anchorY="middle"
                >
                    AGENT CORE
                </Text>
            </Float>
        </group>
    );
}
