<script lang="ts">
	import type { CatalogFile } from '$lib/api';
	import EmptyState from './EmptyState.svelte';
	import SampleRow from './SampleRow.svelte';

	let {
		items,
		selectedPath,
		playingPath,
		cached,
		downloadingPath,
		onpreview,
		ontogglePlay,
		ondownload,
		onpointerdown,
		onstopGesture
	}: {
		items: CatalogFile[];
		selectedPath: string | null;
		playingPath: string | null;
		cached: Set<string>;
		downloadingPath: string | null;
		onpreview: (file: CatalogFile) => void;
		ontogglePlay: (file: CatalogFile) => void;
		ondownload: (file: CatalogFile) => void;
		onpointerdown: (event: PointerEvent, file: CatalogFile) => void;
		onstopGesture: (event: Event) => void;
	} = $props();

	let downloadBusy = $derived(downloadingPath !== null);
</script>

{#if items.length === 0}
	<EmptyState text="No samples in the library." />
{:else}
	<div class="overflow-x-auto">
		<table class="table table-pin-rows table-xs table-fixed w-full">
			<thead>
				<tr>
					<th class="w-10"></th>
					<th class="min-w-32">Filename</th>
					<th class="min-w-32">Waveform</th>
					<th class="w-16">Time</th>
					<th class="w-14">Key</th>
					<th class="w-14">BPM</th>
					<th class="w-32"></th>
				</tr>
			</thead>
			<tbody>
				{#each items as file (file.path)}
					<SampleRow
						{file}
						selected={selectedPath === file.path}
						playing={playingPath === file.path}
						cached={cached.has(file.path)}
						downloading={downloadingPath === file.path}
						{downloadBusy}
						{onpreview}
						{ontogglePlay}
						{ondownload}
						{onpointerdown}
						{onstopGesture}
					/>
				{/each}
			</tbody>
		</table>
	</div>
{/if}
