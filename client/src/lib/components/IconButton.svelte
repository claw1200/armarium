<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		label,
		tip = label,
		active = false,
		disabled = false,
		onclick,
		children
	}: {
		label: string;
		tip?: string;
		active?: boolean;
		disabled?: boolean;
		onclick?: (event: MouseEvent) => void;
		children: Snippet;
	} = $props();
</script>

<div class="tooltip" data-tip={tip}>
	<button
		type="button"
		class={['btn btn-ghost btn-square btn-xs', active && 'btn-active']}
		aria-label={label}
		{disabled}
		{onclick}
	>
		{@render children()}
	</button>
</div>
