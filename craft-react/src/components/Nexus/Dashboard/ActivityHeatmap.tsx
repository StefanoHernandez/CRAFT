import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Instance, Instances } from '@react-three/drei';
import { Color, MathUtils } from 'three';

export function ActivityHeatmap() {
    const gridSize = 10;
    const count = gridSize * gridSize;

    // Generate grid data
    const data = useMemo(() => {
        return Array.from({ length: count }, (_, i) => ({
            x: (i % gridSize) - gridSize / 2 + 0.5,
            z: Math.floor(i / gridSize) - gridSize / 2 + 0.5,
            y: 0,
            scale: Math.random(),
            speed: Math.random() * 0.5 + 0.5,
        }));
    }, []);

    return (
        <group position={[0, -1, 0]}>
            <Instances range={count}>
                <boxGeometry args={[0.8, 1, 0.8]} />
                <meshStandardMaterial color="#4f46e5" />

                {data.map((d, i) => (
                    <HeatmapCell key={i} {...d} />
                ))}
            </Instances>
        </group>
    );
}

function HeatmapCell({ x, z, scale, speed }: any) {
    const ref = useRef<any>(null);
    const color = useMemo(() => new Color(), []);

    useFrame((state) => {
        if (!ref.current) return;

        // Animate height
        const t = state.clock.getElapsedTime() * speed;
        const h = Math.sin(t) * 0.5 + 0.5 + scale; // Height between 0.5 and 1.5 + scale

        ref.current.scale.y = h;
        ref.current.position.y = h / 2;

        // Animate color based on height
        const intensity = (h - 0.5) / 2;
        color.setHSL(0.6 - intensity * 0.5, 1, 0.5); // Blue to Green/Yellow
        ref.current.color.copy(color);
    });

    return <Instance ref={ref} position={[x, 0, z]} />;
}
