<script lang="ts">
	import { FACET_LABELS, TAGS_BY_FACET, type TagFacet } from '$lib/tags';

	let {
		facet,
		value,
		onselect
	}: {
		facet: TagFacet;
		value: string;
		onselect: (slug: string) => void;
	} = $props();

	let group = $derived(value);
	let clearLabel = $derived(`Clear ${FACET_LABELS[facet]} tag`);
	let name = $derived(`library-tag-${facet}`);

	function onchange(event: Event): void {
		const target = event.target;
		if (!(target instanceof HTMLInputElement) || target.type !== 'radio') {
			return;
		}
		onselect(target.classList.contains('filter-reset') ? '' : target.value);
	}
</script>

<div class="filter" {onchange}>
	<input
		class="btn btn-xs filter-reset"
		type="radio"
		{name}
		aria-label="×"
		title={clearLabel}
		value=""
		bind:group
	/>
	{#each TAGS_BY_FACET[facet] as tag (tag)}
		<input class="btn btn-xs" type="radio" {name} aria-label={tag} value={tag} bind:group />
	{/each}
</div>
