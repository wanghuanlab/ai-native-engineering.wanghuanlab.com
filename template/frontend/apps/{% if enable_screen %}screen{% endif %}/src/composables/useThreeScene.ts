import * as THREE from 'three'
import { onMounted, onUnmounted, type Ref } from 'vue'

export interface ThreeContext {
  scene: THREE.Scene
  camera: THREE.PerspectiveCamera
  renderer: THREE.WebGLRenderer
  /** 注册每帧回调，参数为距上一帧的秒数 */
  onFrame: (callback: (delta: number) => void) => void
}

/**
 * Three.js 场景的唯一挂载方式。约束：
 * - Three.js 对象一律不放进 ref/reactive，否则 Vue 深度代理会造成严重卡顿；
 * - 组件卸载时自动释放几何体、材质、纹理和渲染器，防止显存泄漏。
 */
export function useThreeScene(
  container: Ref<HTMLElement | undefined>,
  setup: (context: ThreeContext) => void,
): void {
  let renderer: THREE.WebGLRenderer | undefined
  let frameId = 0
  let resizeObserver: ResizeObserver | undefined
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 10_000)
  const frameCallbacks: ((delta: number) => void)[] = []
  const timer = new THREE.Timer()

  onMounted(() => {
    const el = container.value
    if (!el) return
    renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    el.appendChild(renderer.domElement)

    const resize = (): void => {
      const { clientWidth, clientHeight } = el
      if (!renderer || clientWidth === 0 || clientHeight === 0) return
      camera.aspect = clientWidth / clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(clientWidth, clientHeight)
    }
    resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(el)
    resize()

    setup({ scene, camera, renderer, onFrame: (cb) => frameCallbacks.push(cb) })

    const loop = (time: number): void => {
      frameId = requestAnimationFrame(loop)
      timer.update(time)
      const delta = timer.getDelta()
      frameCallbacks.forEach((cb) => cb(delta))
      renderer?.render(scene, camera)
    }
    frameId = requestAnimationFrame(loop)
  })

  onUnmounted(() => {
    cancelAnimationFrame(frameId)
    resizeObserver?.disconnect()
    disposeScene(scene)
    renderer?.dispose()
    renderer?.domElement.remove()
    renderer = undefined
  })
}

export function disposeScene(scene: THREE.Scene): void {
  scene.traverse((object) => {
    const mesh = object as THREE.Mesh
    mesh.geometry?.dispose()
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material]
    for (const material of materials) {
      if (!material) continue
      for (const value of Object.values(material)) {
        if (value instanceof THREE.Texture) value.dispose()
      }
      material.dispose()
    }
  })
  scene.clear()
}
