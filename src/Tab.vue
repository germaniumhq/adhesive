<template>
  <li :class="cssClasses" @click="onclick">
    <button class="pf-c-tabs__link"><slot></slot></button>
    <slot name="drag-container">
      <DragContainer :model="this"/>
    </slot>
  </li>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'

import Icon from './Icon.vue'
import DragContainer from './DragContainer.vue'

/**
 * A tab inside the Tabs. The actual label component comes from the
 * default slot.
 *
 * The drag-container can also be overwritten via the slot with the
 * same name. Implicitly as a model it contains the tab data itself.
 */
@Component({
  components: {
    DragContainer,
    Icon
  }
})
export default class Tab extends Vue {
    @Prop() active!: boolean
    @Prop({ default: '' }) icon!: string

    get cssClasses () {
      const result: {[name: string] : boolean} = {
        'pf-c-tabs__item': true
      }

      if (this.active) {
        result['pf-m-current'] = true
      }

      return result
    }

    onclick (ev: MouseEvent) {
      this.$emit('click', ev)
    }
}
</script>
