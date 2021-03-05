<template>
  <div class="pf-c-toggle-group__item">
    <button :class="[
        'pf-c-toggle-group__button',
        selected ? 'pf-m-selected' : '',
        disabled ? 'pf-m-disabled' : '',
        ]" type="button"
        @click="$emit('click')">
      <Icon :icon="icon"/>
    </button>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'
import Icon from './Icon.vue'

@Component({
  components: { Icon }
})
export default class ToggleButton extends Vue {
  @Prop({}) selected!: boolean
  @Prop({}) disabled!: boolean
  @Prop({}) icon!: string
}
</script>
