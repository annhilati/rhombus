import { useEffect, useState, forwardRef, useImperativeHandle, useRef } from 'react';
import { Layout, Model, TabNode, Actions, IJsonModel, DockLocation } from 'flexlayout-react';
import 'flexlayout-react/style/dark.css';

import FileviewPane from './FileviewPane';
import { fileKey, normalizeRegistryName, prettyRegistryTitle } from '../lib/registry';
import type { RhombusContextFile } from '../types';

interface WorkspaceProps {
    files: RhombusContextFile[];
    selectedFile: RhombusContextFile | null;
    onSelectFile: (file: RhombusContextFile) => void;
}

const INITIAL_LAYOUT: IJsonModel = {
    global: {
        tabEnableClose: true,
        tabSetEnableMaximize: true,
        tabSetTabLocation: "top",
    },
    borders: [],
    layout: {
        type: "row",
        id: "workspace-root",
        weight: 100,
        children: [
            {
                type: "tabset",
                id: "main-tabset",
                weight: 100,
                children: []
            }
        ]
    }
};

const TabContentWrapper = ({ node, files, onSelectFile }: { node: TabNode, files: RhombusContextFile[], onSelectFile: (file: RhombusContextFile) => void }) => {
    const config = node.getConfig();
    const [viewMode, setViewMode] = useState(config.viewMode || 'combined');

    const updateMode = (mode: string) => {
        setViewMode(mode);
        node.getModel().doAction(Actions.updateNodeAttributes(node.getId(), { 
            config: { ...config, viewMode: mode } 
        }));
    };

    const key = config.fileKey;
    const file = files.find(f => fileKey(f) === key);
    
    if (!file) return <div className="workspace-empty">File not found</div>;

    const registryLabel = normalizeRegistryName(file.registry);
    const VisualizerComponent = window.rhombus.visualizers.get(file.registry) || window.rhombus.visualizers.get(registryLabel || '');
    const hasVisualizer = !!VisualizerComponent;
    const effectiveViewMode = hasVisualizer ? viewMode : 'file';

    return (
        <div>
        {/* <div className="pane-header">
            <div className="pane-title">{prettyRegistryTitle(file.registry)}</div>
            <div className="pane-meta">{file.id} ({file.language})</div>
        </div> */}
        <div className={`workspace-tab-content mode-${effectiveViewMode}`}>
            {(effectiveViewMode === 'combined' || effectiveViewMode === 'file') && (
                <div className="pane-container file-pane">
                    <FileviewPane file={file} contextFiles={files} onSelectFile={onSelectFile} />
                </div>
            )}
            
            {(effectiveViewMode === 'combined' || effectiveViewMode === 'visualizer') && VisualizerComponent && (
                <div className="pane-container visualizer-pane">
                    <VisualizerComponent file={file} contextFiles={files} />
                </div>
            )}

            {hasVisualizer && (
                <div className="floating-mode-selector">
                    <div className="mode-sphere">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                             <path d="M2 12C2 12 5 5 12 5C19 5 22 12 22 12C22 12 19 19 12 19C5 19 2 12 2 12Z"></path>
                             <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                    </div>
                    <div className="mode-selector-menu">
                         <button className={viewMode === 'combined' ? 'active' : ''} onClick={() => updateMode('combined')}>File & Visualizer</button>
                         <button className={viewMode === 'file' ? 'active' : ''} onClick={() => updateMode('file')}>File Only</button>
                         <button className={viewMode === 'visualizer' ? 'active' : ''} onClick={() => updateMode('visualizer')}>Visualizer</button>
                    </div>
                </div>
            )}
        </div>
        </div>
    );
};

export interface WorkspaceRef {
    openFile: (file: RhombusContextFile, newTab: boolean) => void;
}

const Workspace = forwardRef<WorkspaceRef, WorkspaceProps>(({ files, selectedFile, onSelectFile }, ref) => {
    const [model] = useState(() => {
        try {
            const saved = localStorage.getItem('rhombus.workspace');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed.global) {
                    parsed.global.splitterSize = 1;
                    parsed.global.splitterExtra = 6;
                }
                return Model.fromJson(parsed);
            }
        } catch (e) {
            console.warn("Could not load saved workspace layout", e);
        }
        return Model.fromJson(INITIAL_LAYOUT);
    });
    const hasLoadedInitial = useRef(false);

    useEffect(() => {
        // Collect tabs that have no file anymore
        const nodesToRemove: string[] = [];
        model.visitNodes((node) => {
            if (node.getType() === 'tab') {
                const tabNode = node as TabNode;
                const config = tabNode.getConfig();
                const key = config?.fileKey;
                if (key && !files.find(f => fileKey(f) === key)) {
                    nodesToRemove.push(node.getId());
                }
            }
        });

        // Remove tabs that have no file anymore
        nodesToRemove.forEach(id => {
            model.doAction(Actions.deleteTab(id));
        });
    }, [files, model]);

    useImperativeHandle(ref, () => ({
        openFile: (file: RhombusContextFile, newTab: boolean) => {
            const key = fileKey(file);
            const existingNode = model.getNodeById(key);
            
            if (existingNode) {
                model.doAction(Actions.selectTab(key));
                return;
            }
            
            const activeTabset = model.getActiveTabset();
            const tabsetId = activeTabset ? activeTabset.getId() : 'main-tabset';
            
            if (newTab) {
                model.doAction(Actions.addTab({
                    type: 'tab',
                    component: 'file-tab',
                    id: key,
                    name: file.id,
                    config: { fileKey: key, viewMode: 'combined' }
                }, tabsetId, DockLocation.CENTER, -1, true));
            } else {
                const activeTab = activeTabset?.getSelectedNode() as TabNode | undefined;
                if (activeTab) {
                    const currentViewMode = activeTab.getConfig()?.viewMode || 'combined';
                    const index = activeTab.getParent()!.getChildren().indexOf(activeTab);
                    
                    model.doAction(Actions.addTab({
                        type: 'tab',
                        component: 'file-tab',
                        id: key,
                        name: file.id,
                        config: { fileKey: key, viewMode: currentViewMode }
                    }, tabsetId, DockLocation.CENTER, index, true));
                    
                    model.doAction(Actions.deleteTab(activeTab.getId()));
                } else {
                    model.doAction(Actions.addTab({
                        type: 'tab',
                        component: 'file-tab',
                        id: key,
                        name: file.id,
                        config: { fileKey: key, viewMode: 'combined' }
                    }, tabsetId, DockLocation.CENTER, -1, true));
                }
            }
        }
    }));

    useEffect(() => {
        if (selectedFile && !hasLoadedInitial.current) {
            hasLoadedInitial.current = true;
            const key = fileKey(selectedFile);
            const name = selectedFile.id || 'Unknown';
            
            if (!model.getNodeById(key)) {
                model.doAction(Actions.addTab({
                    type: 'tab',
                    component: 'file-tab',
                    id: key,
                    name: name,
                    config: { fileKey: key, viewMode: 'combined' }
                }, 'main-tabset', DockLocation.CENTER, -1, true));
            }
        }
    }, [selectedFile, model]);

    const factory = (node: TabNode) => {
        return <TabContentWrapper node={node} files={files} onSelectFile={onSelectFile} />;
    };

    const onExternalDrag = (e: React.DragEvent<HTMLElement>) => {
        const file = (window as any).__draggedRhombusFile as RhombusContextFile | undefined;
        if (file) {
            const key = fileKey(file);
            const existingNode = model.getNodeById(key);
            const tabId = existingNode ? ((window as any).__draggedRhombusTabId || key + '-' + Date.now()) : key;
            const name = file.id || 'Unknown';
            
            return {
                json: {
                    type: 'tab',
                    component: 'file-tab',
                    id: tabId,
                    name: name,
                    config: { fileKey: key, viewMode: 'combined' }
                },
                onDrop: () => {
                    (window as any).__draggedRhombusFile = null;
                    (window as any).__draggedRhombusTabId = null;
                }
            };
        }
        return undefined;
    };

    return (
        <div className="workspace-container">
            <Layout 
                model={model} 
                factory={factory} 
                onExternalDrag={onExternalDrag}
                realtimeResize={true}
                onModelChange={(model: Model) => {localStorage.setItem('rhombus.workspace', JSON.stringify(model.toJson()))}}
            />
        </div>
    );
});

export default Workspace;
