import React from 'react';
import { BuildingBlock } from './BuildingBlock';
import { Float, Grid } from '@react-three/drei';

export function CityLayout() {
    return (
        <group>
            {/* Floor Grid */}
            <Grid
                position={[0, -0.01, 0]}
                args={[20, 20]}
                cellSize={1}
                cellThickness={0.5}
                cellColor="#1e293b"
                sectionSize={5}
                sectionThickness={1}
                sectionColor="#334155"
                fadeDistance={20}
                infiniteGrid
            />

            {/* CORE DISTRICT (Center) */}
            <group position={[0, 0, 0]}>
                <BuildingBlock
                    position={[0, 0, 0]}
                    height={4}
                    color="#3b82f6" // Blue
                    label="AGENT CORE"
                    subLabel="Orchestrator"
                />
                <BuildingBlock
                    position={[-2, 0, 0]}
                    height={2.5}
                    color="#06b6d4" // Cyan
                    label="MEMORY"
                    subLabel="Vector Store"
                />
                <BuildingBlock
                    position={[2, 0, 0]}
                    height={2.5}
                    color="#f59e0b" // Amber
                    label="TOOLS"
                    subLabel="Function Registry"
                />
            </group>

            {/* PROVIDER DISTRICT (North) */}
            <group position={[0, 0, -4]}>
                <BuildingBlock
                    position={[0, 0, 0]}
                    height={3}
                    color="#ec4899" // Pink
                    label="LLM GATEWAY"
                    subLabel="Provider Abstraction"
                />
                <BuildingBlock
                    position={[-1.5, 0, 1.5]}
                    height={1.5}
                    color="#10b981" // Green
                    label="OpenAI"
                />
                <BuildingBlock
                    position={[1.5, 0, 1.5]}
                    height={1.5}
                    color="#8b5cf6" // Purple
                    label="Anthropic"
                />
                <BuildingBlock
                    position={[0, 0, 2.5]}
                    height={1.5}
                    color="#ef4444" // Red
                    label="Google"
                />
            </group>

            {/* RAG DISTRICT (West) */}
            <group position={[-5, 0, 0]}>
                <BuildingBlock
                    position={[0, 0, 0]}
                    height={3}
                    color="#6366f1" // Indigo
                    label="RAG PIPELINE"
                />
                <BuildingBlock
                    position={[0, 0, 1.5]}
                    height={2}
                    color="#818cf8"
                    label="Embeddings"
                />
                <BuildingBlock
                    position={[0, 0, -1.5]}
                    height={2}
                    color="#818cf8"
                    label="Reranker"
                />
            </group>

            {/* API DISTRICT (East) */}
            <group position={[5, 0, 0]}>
                <BuildingBlock
                    position={[0, 0, 0]}
                    height={2.5}
                    color="#14b8a6" // Teal
                    label="API SERVER"
                    subLabel="FastAPI"
                />
                <BuildingBlock
                    position={[0, 0, 1.5]}
                    height={1.5}
                    color="#2dd4bf"
                    label="WebSocket"
                />
            </group>

            {/* Flying Cars / Data Packets */}
            <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
                <mesh position={[2, 3, 2]}>
                    <coneGeometry args={[0.1, 0.3, 4]} rotation={[Math.PI / 2, 0, 0]} />
                    <meshBasicMaterial color="#fbbf24" />
                </mesh>
            </Float>
        </group>
    );
}
