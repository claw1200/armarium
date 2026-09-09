<script lang="ts">
	import { resolve } from '$app/paths';

	let {
		pageNumber,
		pageCount,
		previousHref,
		nextHref,
		hasPrevious,
		hasNext
	}: {
		pageNumber: number;
		pageCount: number;
		previousHref: '/' | `/?${string}`;
		nextHref: '/' | `/?${string}`;
		hasPrevious: boolean;
		hasNext: boolean;
	} = $props();
</script>

<div class="join">
	{#if hasPrevious}
		<a class="join-item btn" href={resolve(previousHref)} aria-label="Previous page">«</a>
	{:else}
		<button type="button" class="join-item btn" disabled aria-label="Previous page">«</button>
	{/if}
	<button type="button" class="join-item btn" disabled>{pageNumber} / {pageCount}</button>
	{#if hasNext}
		<a class="join-item btn" href={resolve(nextHref)} aria-label="Next page">»</a>
	{:else}
		<button type="button" class="join-item btn" disabled aria-label="Next page">»</button>
	{/if}
</div>
