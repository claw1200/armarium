<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		label,
		tip = label,
		active = false,
		disabled = false,
		onclick,
		onpointerdown,
		children
	}: {
		label: string;
		tip?: string;
		active?: boolean;
		disabled?: boolean;
		onclick?: (event: MouseEvent) => void;
		onpointerdown?: (event: PointerEvent) => void;
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
		{onpointerdown}
	>
		{@render children()}
	</button>
</div>
