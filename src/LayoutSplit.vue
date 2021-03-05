<template>
  <div class="pf-l-split pf-m-gutter">
    <div class="pf-l-split__item" v-if="$slots.left_content"><slot name="left_content"></slot></div>
    <div class="pf-l-split__item pf-m-fill"><slot></slot></div>
    <div class="pf-l-split__item" v-if="$slots.right_content"><slot name="right_content"></slot></div>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator'

@Component({})
export default class LayoutSplit extends Vue {
}
</script>
