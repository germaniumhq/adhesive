<template>
  <div class="pf-l-flex__item">
    <slot></slot>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator'

@Component({})
export default class FlexItem extends Vue {
}
</script>
