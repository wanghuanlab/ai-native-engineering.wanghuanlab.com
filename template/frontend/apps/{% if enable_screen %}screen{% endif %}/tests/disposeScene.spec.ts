import { disposeScene } from '@/composables/useThreeScene'
import * as THREE from 'three'
import { describe, expect, it, vi } from 'vitest'

describe('disposeScene', () => {
  it('释放几何体与材质并清空场景', () => {
    const scene = new THREE.Scene()
    const geometry = new THREE.BoxGeometry()
    const material = new THREE.MeshBasicMaterial()
    scene.add(new THREE.Mesh(geometry, material))
    const geometrySpy = vi.spyOn(geometry, 'dispose')
    const materialSpy = vi.spyOn(material, 'dispose')

    disposeScene(scene)

    expect(geometrySpy).toHaveBeenCalled()
    expect(materialSpy).toHaveBeenCalled()
    expect(scene.children).toHaveLength(0)
  })
})
