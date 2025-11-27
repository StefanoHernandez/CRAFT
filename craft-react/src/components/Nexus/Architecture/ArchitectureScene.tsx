import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, PerspectiveCamera, Environment } from '@react-three/drei';
import { EffectComposer, Bloom, TiltShift } from '@react-three/postprocessing';
import { CityLayout } from './CityLayout';

export function ArchitectureScene() {
    return (
        <div className="w-full h-screen bg-slate-950 overflow-hidden">
            <Canvas shadows>
                <PerspectiveCamera makeDefault position={[10, 10, 10]} fov={50} />
                <OrbitControls
                    maxPolarAngle={Math.PI / 2.1} // Don't allow going below ground
                    minDistance={5}
                    maxDistance={30}
                    autoRotate
                    autoRotateSpeed={0.5}
                />

                {/* Lighting */}
                <ambientLight intensity={0.2} />
                <pointLight position={[10, 10, 10]} intensity={1} castShadow />
                <pointLight position={[-10, 10, -10]} intensity={0.5} color="#4f46e5" />

                {/* Environment */}
                <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
                <fog attach="fog" args={['#0f172a', 10, 40]} />

                {/* Scene Content */}
                <Suspense fallback={null}>
                    <group position={[0, -1, 0]}>
                        <CityLayout />
                    </group>
                </Suspense>

                {/* Post Processing */}
                <EffectComposer>
                    <Bloom luminanceThreshold={0.5} luminanceSmoothing={0.9} height={300} intensity={1.5} />
                    <TiltShift />
                </EffectComposer>
            </Canvas>

            {/* Overlay Title */}
            <div className="absolute top-8 left-8 pointer-events-none">
                <h1 className="text-4xl font-bold text-white tracking-tighter">CRAFT CITY</h1>
                <p className="text-blue-400 font-mono text-sm tracking-widest">ARCHITECTURE EXPLORER</p>
            </div>
        </div>
    );
}
