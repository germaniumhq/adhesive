<template>
  <span class="pf-c-label pf-m-blue">
    <span class="pf-c-label__content">
      <slot></slot>
      <button class="pf-c-button pf-m-plain"
              type="button"
              id="outline-grey-icon-close-button"
              aria-label="Remove"
              aria-labelledby="outline-grey-icon-close-button outline-grey-icon-close-text"
              v-if="removable">
        <i class="fas fa-times" aria-hidden="true"></i>
      </button>
    </span>
  </span>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator'

@Component({})
export default class Label extends Vue {
  removable: boolean = false
}
</script>
