<template>
  <div class="slidev-layout sf-section">
    <div class="sf-section-num">{{ $frontmatter.num }}</div>
    <div class="sf-section-body">
      <slot />
    </div>
  </div>
</template>
