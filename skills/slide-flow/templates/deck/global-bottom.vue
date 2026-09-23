<template>
  <div v-if="$nav.currentLayout !== 'cover'" class="sf-pageno">{{ $nav.currentPage }} / {{ $nav.total }}</div>
</template>
