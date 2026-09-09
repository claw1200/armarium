<script lang="ts">
	import Icon from './Icon.svelte';

	let { onstopGesture }: { onstopGesture: (event: Event) => void } = $props();
</script>

<details class="dropdown dropdown-end">
	<summary
		class="btn btn-ghost btn-square btn-xs"
		aria-label="Sample actions"
		onpointerdown={onstopGesture}
		onclick={onstopGesture}
	>
		<Icon name="more" />
	</summary>
	<ul class="dropdown-content menu rounded-box bg-base-100 z-30 w-40 p-2 shadow">
		<li>
			<button type="button" onpointerdown={onstopGesture} onclick={onstopGesture}>Rename</button>
		</li>
		<li>
			<button type="button" onpointerdown={onstopGesture} onclick={onstopGesture}>Delete</button>
		</li>
		<li>
			<button type="button" onpointerdown={onstopGesture} onclick={onstopGesture}>Show in folder</button>
		</li>
	</ul>
</details>
