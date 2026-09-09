<script lang="ts">
	import type { CatalogFile } from '$lib/api';
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
	<div role="alert" class="alert">No samples in the library.</div>
{:else}
	<div class="overflow-x-auto">
		<table class="table table-pin-rows table-xs">
			<thead>
				<tr>
					<th></th>
					<th>Filename</th>
					<th>Waveform</th>
					<th>Time</th>
					<th>Key</th>
					<th>BPM</th>
					<th></th>
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
