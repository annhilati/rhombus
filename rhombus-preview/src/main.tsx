import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.scss'
import './lib/deepslate-patch'
import * as deepslate from 'deepslate'
import VisualizerPane from './components/VisualizerPane'

window.rhombus = {
  React,
  deepslate,
  densityFunctions: new Map(),
  visualizers: new Map([
    ['worldgen/density_function', VisualizerPane],
    ['worldgen/noise', VisualizerPane]
  ]),
}

const originalFromJson = deepslate.DensityFunction.fromJson
deepslate.DensityFunction.fromJson = function (obj: any, inputParser?: any) {
  const parser = inputParser ?? deepslate.DensityFunction.fromJson
  const type = obj?.type?.replace(/^minecraft:/, '')
  if (type && window.rhombus.densityFunctions.has(type)) {
    return window.rhombus.densityFunctions.get(type)!(obj, parser)
  }
  return originalFromJson.call(this, obj, parser)
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
