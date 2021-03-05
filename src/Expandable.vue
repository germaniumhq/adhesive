<template>
<div :class="cssClasses">
  <button type="button"
          class="pf-c-expandable-section__toggle"
          :aria-expanded="expandedState"
          @click.stop="onClick">
    <span class="pf-c-expandable-section__toggle-icon">
      <i class="fas fa-angle-right" aria-hidden="true"></i>
    </span>
    <span class="pf-c-expandable-section__toggle-text">{{ label }}</span>
  </button>
  <div class="pf-c-expandable__content" v-if="expandedState"><slot>slot-default</slot></div>
</div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'

@Component({})
export default class Expandable extends Vue {
    @Prop() expanded! : boolean
    @Prop() label! : string

    expandedState: boolean = false

    beforeMount () {
      this.expandedState = this.expanded
    }

    onClick () {
      this.expandedState = !this.expandedState

      if (this.expandedState) {
        this.$emit('expand')
      } else {
        this.$emit('collapse')
      }
    }

    get cssClasses () {
      return {
        'pf-c-expandable-section': true,
        'pf-m-expanded': this.expandedState
      }
    }
}
</script>
