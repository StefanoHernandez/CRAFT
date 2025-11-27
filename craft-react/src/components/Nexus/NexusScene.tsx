import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, PerspectiveCamera } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { AgentCore } from './AgentCore';
import { ProviderNode, ToolNode, MemoryNode } from './Nodes';
import { DataFlow } from './DataFlow';

export function NexusScene() {
    return (
        <div className="w-full h-full bg-slate-950">
            <Canvas>
                <PerspectiveCamera makeDefault position={[0, 2, 6]} />
                <OrbitControls
                    enablePan={false}
                    maxPolarAngle={Math.PI / 1.5}
                    minDistance={3}
                    maxDistance={10}
                />

                {/* Lighting */}
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} intensity={1} />
                <pointLight position={[-10, -10, -10]} intensity={0.5} color="#4f46e5" />

                {/* Environment */}
                <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />

                {/* Scene Content */}
                <Suspense fallback={null}>
                    <group position={[0, -0.5, 0]}>
                        <AgentCore />
                        <ProviderNode />
                        <ToolNode />
                        <MemoryNode />
                        <DataFlow />
                    </group>
                </Suspense>

                {/* Post Processing */}
                <EffectComposer>
                    <Bloom luminanceThreshold={0.5} luminanceSmoothing={0.9} height={300} intensity={1.5} />
                </EffectComposer>
            </Canvas>
        </div>
    );
}
