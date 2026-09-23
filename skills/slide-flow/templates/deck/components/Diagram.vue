<script setup>
const props = defineProps({
  src: { type: String, required: true },
  h: { type: [String, Number], default: 360 },
  caption: { type: String, default: '' },
})
const url = `/diagrams/${props.src}.svg`
</script>

<template>
  <figure class="sf-diagram">
    <img :src="url" :style="{ maxHeight: `${h}px` }" :alt="caption || src">
    <figcaption v-if="caption">{{ caption }}</figcaption>
  </figure>
</template>
