<script lang="ts">
	import { waveformAmplitudes } from '$lib/waveform';

	let { seed }: { seed: string } = $props();

	let bars = $derived(waveformAmplitudes(seed));
</script>

<svg
	class="text-base-content/30 h-6 w-full"
	viewBox="0 0 {bars.length} 32"
	preserveAspectRatio="none"
	aria-hidden="true"
>
	{#each bars as amplitude, index (index)}
		<rect
			x={index}
			y={16 - amplitude * 14}
			width="0.7"
			height={amplitude * 28}
			rx="0.2"
			fill="currentColor"
		/>
	{/each}
</svg>
