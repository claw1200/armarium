<script lang="ts">
	import type { CatalogFile } from '$lib/api';
	import { fileStem, formatAudioFormat, formatDuration } from '$lib/format';
	import { missingMeta } from '$lib/placeholders';
	import Icon from './Icon.svelte';
	import IconButton from './IconButton.svelte';
	import OverflowMenu from './OverflowMenu.svelte';
	import Waveform from './Waveform.svelte';

	let {
		file,
		selected,
		playing,
		cached,
		downloading,
		downloadBusy,
		onpreview,
		ontogglePlay,
		ondownload,
		onpointerdown,
		onstopGesture
	}: {
		file: CatalogFile;
		selected: boolean;
		playing: boolean;
		cached: boolean;
		downloading: boolean;
		downloadBusy: boolean;
		onpreview: (file: CatalogFile) => void;
		ontogglePlay: (file: CatalogFile) => void;
		ondownload: (file: CatalogFile) => void;
		onpointerdown: (event: PointerEvent, file: CatalogFile) => void;
		onstopGesture: (event: Event) => void;
	} = $props();

	let liked = $state('');
	let title = $derived(fileStem(file.name));
	let playLabel = $derived(playing ? 'Pause' : 'Play');
	let likeName = $derived(`like-${file.path}`);

	function stopAndToggle(event: MouseEvent): void {
		event.stopPropagation();
		ontogglePlay(file);
	}

	function stopAndDownload(event: MouseEvent): void {
		event.stopPropagation();
		void ondownload(file);
	}

	function onRowKeydown(event: KeyboardEvent): void {
		if (event.key !== 'Enter' && event.key !== ' ') {
			return;
		}
		event.preventDefault();
		onpreview(file);
	}
</script>

<tr
	data-path={file.path}
	class={[cached ? 'cursor-grab' : 'cursor-pointer', selected && 'bg-base-200', 'focus:outline-none']}
	tabindex="-1"
	onpointerdown={(event) => onpointerdown(event, file)}
	onclick={() => onpreview(file)}
	onkeydown={onRowKeydown}
>
	<td class="w-8">
		<div class="tooltip" data-tip={playLabel}>
			<button
				type="button"
				class={['btn btn-ghost btn-square btn-xs swap', playing && 'swap-active']}
				aria-label={playLabel}
				onpointerdown={onstopGesture}
				onclick={stopAndToggle}
			>
				<Icon name="pause" class="swap-on size-4" />
				<Icon name="play" class="swap-off size-4" />
			</button>
		</div>
	</td>
	<td class="w-full max-w-0">
		<div class="flex min-w-0 flex-col gap-1">
			<span class="truncate font-medium">{title}</span>
			<span class="flex min-w-0 items-center gap-1">
				<span class="truncate text-xs opacity-60">{file.parent_path || 'Library'}</span>
				<span class="badge badge-ghost badge-xs shrink-0">{formatAudioFormat(file.format)}</span>
			</span>
		</div>
	</td>
	<td class="w-36 min-w-20">
		<Waveform seed={file.path} />
	</td>
	<td class="whitespace-nowrap tabular-nums opacity-70">{formatDuration(file.duration_seconds)}</td>
	<td class="whitespace-nowrap opacity-70">{missingMeta}</td>
	<td class="whitespace-nowrap opacity-70">{missingMeta}</td>
	<td class="whitespace-nowrap">
		<div class="flex items-center justify-end">
			<div class="tooltip" data-tip={liked ? 'Unlike' : 'Like'}>
				<div class="rating rating-xs">
					<input
						type="radio"
						name={likeName}
						class="rating-hidden"
						aria-label="Unlike"
						value=""
						bind:group={liked}
						onpointerdown={onstopGesture}
						onclick={onstopGesture}
					/>
					<input
						type="radio"
						name={likeName}
						class="mask mask-heart"
						aria-label="Like"
						value="liked"
						bind:group={liked}
						onpointerdown={onstopGesture}
						onclick={onstopGesture}
					/>
				</div>
			</div>
			{#if cached}
				<div class="tooltip" data-tip="Cached">
					<span class="status status-success" aria-label="Cached"></span>
				</div>
			{:else}
				<IconButton label="Download" disabled={downloadBusy} onclick={stopAndDownload}>
					{#if downloading}
						<span class="loading loading-spinner loading-xs" aria-label="Downloading"></span>
					{:else}
						<Icon name="download" />
					{/if}
				</IconButton>
			{/if}
			<OverflowMenu {onstopGesture} />
		</div>
	</td>
</tr>
