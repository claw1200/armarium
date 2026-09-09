<script lang="ts">
	import Icon from './Icon.svelte';

	let { value = $bindable(''), loading = false }: { value?: string; loading?: boolean } = $props();
</script>

<label class="input input-sm w-full">
	<Icon name="search" class="size-4 opacity-50" />
	<input type="search" placeholder="Search samples" autocomplete="off" bind:value />
	{#if loading}
		<span class="loading loading-spinner loading-xs" aria-label="Loading"></span>
	{/if}
</label>
