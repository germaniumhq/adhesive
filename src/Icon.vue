<template>
    <i v-if="icon" :class="cssClasses" @click="onClick"></i>
</template>

<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator'

@Component({})
export default class Icon extends Vue {
    @Prop() icon!: string
    @Prop() _class!: string

    get cssClasses () {
      let result = `fas ${this.icon}`

      if (this._class) {
        result += ` ${this._class}`
      }

      return result
    }

    onClick () {
      this.$emit('click')
    }
}
</script>
