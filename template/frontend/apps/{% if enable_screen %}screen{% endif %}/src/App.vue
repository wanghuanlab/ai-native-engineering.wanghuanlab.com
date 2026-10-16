<template>
  <div ref="container" class="screen" />
</template>

<script setup lang="ts">
import { useThreeScene } from '@/composables/useThreeScene'
import * as THREE from 'three'
import { ref } from 'vue'

const container = ref<HTMLElement>()

useThreeScene(container, ({ scene, camera, onFrame }) => {
  camera.position.set(4, 3, 6)
  camera.lookAt(0, 0, 0)

  scene.add(new THREE.AmbientLight(0xffffff, 0.6))
  const light = new THREE.DirectionalLight(0xffffff, 1)
  light.position.set(5, 10, 7)
  scene.add(light)

  const cube = new THREE.Mesh(
    new THREE.BoxGeometry(2, 2, 2),
    new THREE.MeshStandardMaterial({ color: 0x3a8ee6 }),
  )
  scene.add(cube)

  onFrame((delta) => {
    cube.rotation.y += delta * 0.5
  })
})
</script>

<style>
html,
body,
#app {
  margin: 0;
  height: 100%;
  background: #0b1a2e;
}
.screen {
  width: 100%;
  height: 100%;
}
</style>
