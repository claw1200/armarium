<script lang="ts">
	import { filterGroups, filterTags, sortOptions } from '$lib/placeholders';

	let { resultLabel }: { resultLabel: string } = $props();

	let selectedFilters = $state<Record<string, string>>(
		Object.fromEntries(filterGroups.map((group) => [group.id, '']))
	);
	let selectedTag = $state('');
	let sort = $state<(typeof sortOptions)[number]>(sortOptions[0]);

	let hasFilters = $derived(Object.values(selectedFilters).some(Boolean) || selectedTag !== '');

	function clearFilters(): void {
		selectedFilters = Object.fromEntries(filterGroups.map((group) => [group.id, '']));
		selectedTag = '';
	}
</script>

<div class="flex flex-col gap-2">
	<div class="flex items-center gap-2">
		<div class="flex min-w-0 flex-1 flex-wrap gap-2">
			{#each filterGroups as group (group.id)}
				<select class="select select-sm w-fit" bind:value={selectedFilters[group.id]}>
					<option value="">{group.label}</option>
					{#each group.options as option (option)}
						<option value={option}>{option}</option>
					{/each}
				</select>
			{/each}
		</div>
		{#if hasFilters}
			<button type="button" class="btn btn-ghost btn-sm shrink-0" onclick={clearFilters}>
				Clear all
			</button>
		{/if}
	</div>

	<form class="filter" onreset={() => (selectedTag = '')}>
		<input class="btn btn-xs btn-square" type="reset" value="×" />
		{#each filterTags as tag (tag)}
			<input
				class="btn btn-xs"
				type="radio"
				name="library-tag"
				aria-label={tag}
				value={tag}
				bind:group={selectedTag}
			/>
		{/each}
	</form>

	<div class="flex items-center justify-between gap-2 text-sm">
		<span class="opacity-80">{resultLabel}</span>
		<select class="select select-ghost select-sm w-fit" bind:value={sort}>
			{#each sortOptions as option (option)}
				<option value={option}>{option}</option>
			{/each}
		</select>
	</div>
</div>
