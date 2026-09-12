<script lang="ts">
	import { BPM_RANGES, KEY_ROOTS } from '$lib/filters';
	import { sortOptions } from '$lib/placeholders';
	import { FACET_ORDER, tagForFacet, type TagFacet } from '$lib/tags';
	import TagFilter from './TagFilter.svelte';

	let {
		resultLabel,
		tags,
		key,
		bpm,
		onfacet,
		onkey,
		onbpm,
		onclear
	}: {
		resultLabel: string;
		tags: string[];
		key: string;
		bpm: string;
		onfacet: (facet: TagFacet, slug: string) => void;
		onkey: (key: string) => void;
		onbpm: (bpm: string) => void;
		onclear: () => void;
	} = $props();

	let sort = $state<(typeof sortOptions)[number]>(sortOptions[0]);
	let hasFilters = $derived(tags.length > 0 || key !== '' || bpm !== '');

	function onKeyChange(event: Event): void {
		if (event.currentTarget instanceof HTMLSelectElement) {
			onkey(event.currentTarget.value);
		}
	}

	function onBpmChange(event: Event): void {
		if (event.currentTarget instanceof HTMLSelectElement) {
			onbpm(event.currentTarget.value);
		}
	}
</script>

<div class="flex flex-col gap-2">
	<div class="flex items-center gap-2">
		<div class="flex min-w-0 flex-1 flex-wrap gap-2">
			<select class="select select-sm w-fit" aria-label="Key" value={key} onchange={onKeyChange}>
				<option value="">Key</option>
				{#each KEY_ROOTS as root (root)}
					<option value={root}>{root}</option>
				{/each}
			</select>
			<select class="select select-sm w-fit" aria-label="BPM" value={bpm} onchange={onBpmChange}>
				<option value="">BPM</option>
				{#each BPM_RANGES as range (range.id)}
					<option value={range.id}>{range.label}</option>
				{/each}
			</select>
		</div>
		{#if hasFilters}
			<button type="button" class="btn btn-ghost btn-sm shrink-0" onclick={onclear}>
				Clear all
			</button>
		{/if}
	</div>

	<div class="flex flex-col gap-2">
		{#each FACET_ORDER as facet (facet)}
			<TagFilter {facet} value={tagForFacet(tags, facet)} onselect={(slug) => onfacet(facet, slug)} />
		{/each}
	</div>

	<div class="flex items-center justify-between gap-2 text-sm">
		<span class="opacity-80">{resultLabel}</span>
		<select class="select select-ghost select-sm w-fit" bind:value={sort}>
			{#each sortOptions as option (option)}
				<option value={option}>{option}</option>
			{/each}
		</select>
	</div>
</div>
