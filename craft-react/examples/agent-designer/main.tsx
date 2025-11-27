/**
 * Demo Example - Visual Agent Designer
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { AgentDesigner } from '../../src/components/AgentDesigner';
import '../../src/styles.css';

function App() {
    return (
        <div className="min-h-screen">
            <AgentDesigner />
        </div>
    );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
