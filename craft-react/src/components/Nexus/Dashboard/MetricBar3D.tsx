import React, { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text } from '@react-three/drei';
import { Mesh } from 'three';

interface MetricBar3DProps {
    position: [number, number, number];
    value: number; // 0 to 100
    label: string;
    color: string;
}

export function MetricBar3D({ position, value, label, color }: MetricBar3DProps) {
    const meshRef = useRef<Mesh>(null);
    const [hovered, setHovered] = useState(false);

    // Animate height based on value
    const targetHeight = Math.max(0.1, (value / 100) * 5); // Max height 5 units

    useFrame((state) => {
        if (!meshRef.current) return;
        // Smooth lerp to target height
        meshRef.current.scale.y += (targetHeight - meshRef.current.scale.y) * 0.1;
        // Adjust position so it grows from bottom
        meshRef.current.position.y = meshRef.current.scale.y / 2;
    });

    return (
        <group position={position}>
            <mesh
                ref={meshRef}
                onPointerOver={() => setHovered(true)}
                onPointerOut={() => setHovered(false)}
            >
                <boxGeometry args={[0.8, 1, 0.8]} />
                <meshStandardMaterial
                    color={color}
                    transparent
                    opacity={0.9}
                    emissive={color}
                    emissiveIntensity={hovered ? 0.8 : 0.2}
                />
            </mesh>

            {/* Label */}
            <Text
                position={[0, -0.5, 0.5]}
                rotation={[-Math.PI / 4, 0, 0]}
                fontSize={0.2}
                color="white"
                anchorX="center"
                anchorY="top"
            >
                {label}
            </Text>

            {/* Value Label (floating above) */}
            {hovered && (
                <Text
                    position={[0, targetHeight + 0.5, 0]}
                    fontSize={0.3}
                    color="white"
                    anchorX="center"
                    anchorY="bottom"
                >
                    {value}%
                </Text>
            )}
        </group>
    );
}
