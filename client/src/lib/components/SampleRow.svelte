<script lang="ts">
	import type { CatalogFile } from '$lib/api';
	import { fileStem, formatAudioFormat, formatDuration } from '$lib/format';
	import { missingMeta } from '$lib/placeholders';
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

	let liked = $state(false);
	let title = $derived(fileStem(file.name));
	let playLabel = $derived(playing ? 'Pause' : 'Play');
	let likeLabel = $derived(liked ? 'Unlike' : 'Like');
	let downloadLabel = $derived(downloading ? 'Downloading' : 'Download');

	function stopAndToggle(event: MouseEvent): void {
		event.stopPropagation();
		ontogglePlay(file);
	}

	function stopAndDownload(event: MouseEvent): void {
		event.stopPropagation();
		void ondownload(file);
	}

	function stopAndToggleLike(event: MouseEvent): void {
		event.stopPropagation();
		liked = !liked;
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
	class={[cached ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer', selected && 'bg-base-200', 'focus:outline-none']}
	tabindex="-1"
	onpointerdown={(event) => onpointerdown(event, file)}
	onclick={() => onpreview(file)}
	onkeydown={onRowKeydown}
>
	<td class="w-10">
		<div class="tooltip" data-tip={playLabel}>
			<button
				type="button"
				class={['btn btn-ghost btn-square btn-xs swap', playing && 'swap-active']}
				aria-label={playLabel}
				onpointerdown={onstopGesture}
				onclick={stopAndToggle}
			>
				<span class="icon-[lucide--pause] swap-on size-4" aria-hidden="true"></span>
				<span class="icon-[lucide--play] swap-off size-4" aria-hidden="true"></span>
			</button>
		</div>
	</td>
	<td class="min-w-0">
		<div class="flex min-w-0 flex-col gap-1">
			<span class="truncate font-medium">{title}</span>
			<span class="flex min-w-0 items-center gap-1">
				<span class="truncate text-xs opacity-60">{file.parent_path || 'Library'}</span>
				<span class="badge badge-ghost badge-xs shrink-0">{formatAudioFormat(file.format)}</span>
			</span>
		</div>
	</td>
	<td class="min-w-0">
		<Waveform seed={file.path} />
	</td>
	<td class="whitespace-nowrap tabular-nums opacity-70">{formatDuration(file.duration_seconds)}</td>
	<td class="whitespace-nowrap opacity-70">{missingMeta}</td>
	<td class="whitespace-nowrap opacity-70">{missingMeta}</td>
	<td class="whitespace-nowrap">
		<div class="flex items-center justify-end gap-2">
			<IconButton label={likeLabel} active={liked} onpointerdown={onstopGesture} onclick={stopAndToggleLike}>
				<span
					class={['icon-[lucide--heart] size-4', liked && 'text-error']}
					aria-hidden="true"
				></span>
			</IconButton>
			{#if cached}
				<div class="tooltip" data-tip="Downloaded">
					<span
						class="inline-flex size-6 items-center justify-center"
						aria-label="Downloaded"
					>
						<span class="icon-[lucide--file-check] size-4 text-success" aria-hidden="true"></span>
					</span>
				</div>
			{:else}
				<IconButton
					label={downloadLabel}
					disabled={downloadBusy}
					onpointerdown={onstopGesture}
					onclick={stopAndDownload}
				>
					{#if downloading}
						<span class="icon-[lucide--loader-circle] size-4 animate-spin" aria-hidden="true"></span>
					{:else}
						<span class="icon-[lucide--download] size-4" aria-hidden="true"></span>
					{/if}
				</IconButton>
			{/if}
			<OverflowMenu {onstopGesture} />
		</div>
	</td>
</tr>
