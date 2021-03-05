<template>
  <label class="pf-c-switch" :for="label">
    <input class="pf-c-switch__input"
           type="checkbox"
           @change="$emit('change', $event)"
           @click="$emit('click', $event)"
           :id="label"/>
    <span class="pf-c-switch__toggle">
      <span class="pf-c-switch__toggle-icon">
        <i :class="['fas', icon]" aria-hidden="true"></i>
      </span>
    </span>
  </label>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'

@Component({})
export default class Switcher extends Vue {
  @Prop({}) value!: boolean
  @Prop({}) icon!: string
  @Prop({}) label!: string
}
</script>

<style scoped>
.pf-c-switch__input:not(:checked) ~ .pf-c-switch__toggle .pf-c-switch__toggle-icon {
  display: inherit;
  visibility: inherit;
  left: 22px;
  top: 5px;
  transition: left 0.4s;
}

.pf-c-switch__toggle-icon {
  transition: left 0.4s;
}
</style>
