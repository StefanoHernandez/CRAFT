import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, PerspectiveCamera, Text } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { MetricBar3D } from './MetricBar3D';
import { ActivityHeatmap } from './ActivityHeatmap';

export function DashboardScene() {
    return (
        <div className="w-full h-screen bg-slate-950 overflow-hidden">
            <Canvas>
                <PerspectiveCamera makeDefault position={[8, 8, 8]} fov={50} />
                <OrbitControls
                    maxPolarAngle={Math.PI / 2.1}
                    minDistance={5}
                    maxDistance={20}
                    autoRotate
                    autoRotateSpeed={0.2}
                />

                {/* Lighting */}
                <ambientLight intensity={0.4} />
                <pointLight position={[10, 10, 10]} intensity={1} />
                <pointLight position={[-10, 5, -10]} intensity={0.5} color="#4f46e5" />

                {/* Environment */}
                <Stars radius={100} depth={50} count={3000} factor={4} saturation={0} fade speed={0.5} />
                <gridHelper args={[20, 20, 0x334155, 0x1e293b]} position={[0, -1, 0]} />

                {/* Scene Content */}
                <Suspense fallback={null}>
                    <group position={[0, -0.5, 0]}>

                        {/* Metrics Section */}
                        <group position={[-4, 0, -2]}>
                            <Text position={[0, 4, 0]} fontSize={0.5} color="white">TOKEN USAGE</Text>
                            <MetricBar3D position={[-1.5, 0, 0]} value={85} label="GPT-4o" color="#10b981" />
                            <MetricBar3D position={[0, 0, 0]} value={45} label="Claude" color="#8b5cf6" />
                            <MetricBar3D position={[1.5, 0, 0]} value={20} label="Gemini" color="#ef4444" />
                        </group>

                        <group position={[-4, 0, 2]}>
                            <Text position={[0, 4, 0]} fontSize={0.5} color="white">LATENCY (ms)</Text>
                            <MetricBar3D position={[-1.5, 0, 0]} value={30} label="Avg" color="#3b82f6" />
                            <MetricBar3D position={[0, 0, 0]} value={60} label="P95" color="#f59e0b" />
                            <MetricBar3D position={[1.5, 0, 0]} value={90} label="P99" color="#ef4444" />
                        </group>

                        {/* Heatmap Section */}
                        <group position={[4, 0, 0]}>
                            <Text position={[0, 4, 0]} fontSize={0.5} color="white">SYSTEM ACTIVITY</Text>
                            <ActivityHeatmap />
                        </group>

                    </group>
                </Suspense>

                {/* Post Processing */}
                <EffectComposer>
                    <Bloom luminanceThreshold={0.6} luminanceSmoothing={0.9} height={300} intensity={1.2} />
                </EffectComposer>
            </Canvas>

            {/* Overlay Title */}
            <div className="absolute top-8 left-8 pointer-events-none">
                <h1 className="text-4xl font-bold text-white tracking-tighter">ANALYTICS 3D</h1>
                <p className="text-purple-400 font-mono text-sm tracking-widest">REAL-TIME DASHBOARD</p>
            </div>
        </div>
    );
}
