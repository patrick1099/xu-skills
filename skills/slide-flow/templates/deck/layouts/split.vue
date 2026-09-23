<script setup>
import { computed } from 'vue'
const props = defineProps({
  ratio: { type: String, default: '1/1' },
  heading: { type: String, default: '' },
  valign: { type: String, default: 'top' },
})
const cols = computed(() => {
  const [a, b] = String(props.ratio).split('/').map(Number)
  return `${a || 1}fr ${b || 1}fr`
})
const align = computed(() => (props.valign === 'center' ? 'center' : props.valign === 'bottom' ? 'end' : 'start'))
</script>

<template>
  <div class="slidev-layout sf-split">
    <h1 v-if="heading">{{ heading }}</h1>
    <div class="sf-split-grid" :style="{ gridTemplateColumns: cols, alignItems: align }">
      <div class="sf-split-left"><slot /></div>
      <div class="sf-split-right"><slot name="right" /></div>
    </div>
  </div>
</template>
