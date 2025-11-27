import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh } from 'three';
import { Text, Float } from '@react-three/drei';
import { useNexusStore } from '../../stores/nexusStore';

export function ProviderNode() {
    const meshRef = useRef<Mesh>(null);
    const status = useNexusStore((state) => state.nodes.find((n) => n.id === 'provider')?.status || 'idle');

    useFrame((state) => {
        if (!meshRef.current) return;
        meshRef.current.rotation.y += 0.01;

        if (status === 'active') {
            meshRef.current.rotation.y += 0.05;
        }
    });

    return (
        <group position={[0, 2, -2]}>
            <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.3}>
                <mesh ref={meshRef}>
                    <octahedronGeometry args={[0.8, 0]} />
                    <meshStandardMaterial
                        color="#ec4899" // Pink
                        wireframe
                        emissive="#ec4899"
                        emissiveIntensity={status === 'active' ? 1 : 0.2}
                    />
                </mesh>
                <Text position={[0, -1.2, 0]} fontSize={0.15} color="white">
                    LLM PROVIDER
                </Text>
            </Float>
        </group>
    );
}

export function ToolNode() {
    const groupRef = useRef<any>(null);
    const status = useNexusStore((state) => state.nodes.find((n) => n.id === 'tools')?.status || 'idle');

    useFrame((state) => {
        if (!groupRef.current) return;
        groupRef.current.rotation.z = Math.sin(state.clock.getElapsedTime() * 0.5) * 0.2;
    });

    return (
        <group position={[2, 1, 1]} ref={groupRef}>
            <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
                <mesh>
                    <boxGeometry args={[0.8, 0.8, 0.8]} />
                    <meshStandardMaterial
                        color="#f59e0b" // Amber
                        wireframe
                        emissive="#f59e0b"
                        emissiveIntensity={status === 'active' ? 1 : 0.2}
                    />
                </mesh>
                <Text position={[0, -1.2, 0]} fontSize={0.15} color="white">
                    TOOLS
                </Text>
            </Float>
        </group>
    );
}

export function MemoryNode() {
    const meshRef = useRef<Mesh>(null);
    const status = useNexusStore((state) => state.nodes.find((n) => n.id === 'memory')?.status || 'idle');

    useFrame((state) => {
        if (!meshRef.current) return;
        meshRef.current.rotation.x += 0.005;
        meshRef.current.rotation.z += 0.005;
    });

    return (
        <group position={[-2, 1, 1]}>
            <Float speed={1} rotationIntensity={0.2} floatIntensity={0.2}>
                <mesh ref={meshRef}>
                    <dodecahedronGeometry args={[0.7, 0]} />
                    <meshStandardMaterial
                        color="#06b6d4" // Cyan
                        wireframe
                        emissive="#06b6d4"
                        emissiveIntensity={status === 'active' ? 1 : 0.2}
                    />
                </mesh>
                <Text position={[0, -1.2, 0]} fontSize={0.15} color="white">
                    MEMORY
                </Text>
            </Float>
        </group>
    );
}
