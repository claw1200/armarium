<script lang="ts">
	import { iconPaths, type IconName } from '$lib/icons';

	let { name, class: className = 'size-4' }: { name: IconName; class?: string } = $props();
</script>

<svg
	xmlns="http://www.w3.org/2000/svg"
	viewBox="0 0 24 24"
	fill="currentColor"
	class={className}
	aria-hidden="true"
>
	<path d={iconPaths[name]} />
</svg>
