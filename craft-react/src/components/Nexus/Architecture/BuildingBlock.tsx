import React, { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Edges } from '@react-three/drei';
import { Mesh } from 'three';

interface BuildingBlockProps {
    position: [number, number, number];
    height: number;
    color: string;
    label: string;
    subLabel?: string;
    onClick?: () => void;
}

export function BuildingBlock({ position, height, color, label, subLabel, onClick }: BuildingBlockProps) {
    const meshRef = useRef<Mesh>(null);
    const [hovered, setHovered] = useState(false);

    useFrame((state) => {
        if (!meshRef.current) return;
        // Subtle breathing animation
        meshRef.current.scale.y = 1 + Math.sin(state.clock.getElapsedTime() * 2) * 0.005;
    });

    return (
        <group position={position}>
            {/* Building Body */}
            <mesh
                ref={meshRef}
                position={[0, height / 2, 0]}
                onPointerOver={() => setHovered(true)}
                onPointerOut={() => setHovered(false)}
                onClick={onClick}
            >
                <boxGeometry args={[1, height, 1]} />
                <meshStandardMaterial
                    color={color}
                    transparent
                    opacity={0.8}
                    emissive={color}
                    emissiveIntensity={hovered ? 0.8 : 0.2}
                />
                <Edges color="white" threshold={15} />
            </mesh>

            {/* Label */}
            <group position={[0, height + 0.5, 0]}>
                <Text
                    fontSize={0.15}
                    color="white"
                    anchorX="center"
                    anchorY="bottom"
                    outlineWidth={0.01}
                    outlineColor="#000000"
                >
                    {label}
                </Text>
                {subLabel && (
                    <Text
                        position={[0, -0.2, 0]}
                        fontSize={0.1}
                        color="#94a3b8"
                        anchorX="center"
                        anchorY="top"
                    >
                        {subLabel}
                    </Text>
                )}
            </group>

            {/* Base Glow */}
            <mesh position={[0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                <ringGeometry args={[0.6, 0.8, 32]} />
                <meshBasicMaterial color={color} transparent opacity={0.5} />
            </mesh>
        </group>
    );
}
