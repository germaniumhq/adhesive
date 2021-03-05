<template>
  <div class="pf-c-alert pf-m-success pf-m-inline" aria-label="Success alert">
    <div class="pf-c-alert__icon">
      <i class="fas fa-fw fa-check-circle" aria-hidden="true"></i>
    </div>
    <p class="pf-c-alert__title">
      <strong>
        <slot name="title"></slot>
      </strong>
    </p>
    <div class="pf-c-alert__action" v-if="$slots.actions">
      <slot name="actions"></slot>
    </div>
    <div class="pf-c-alert__description">
      <slot></slot>
    </div>
    <div class="pf-c-alert__action-group">
      <button class="pf-c-button pf-m-link pf-m-inline" type="button">View details</button>
      <button class="pf-c-button pf-m-link pf-m-inline" type="button">Ignore</button>
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator'

@Component({})
export default class Alert extends Vue {
}
</script>
