<script lang="ts">
	import { fly } from 'svelte/transition';
	import type { CatalogFile } from '$lib/api';
	import { fileStem, formatAudioFormat, formatBpm, formatKey } from '$lib/format';
	import IconButton from './IconButton.svelte';

	let {
		sample,
		playing,
		currentTime = $bindable(0),
		duration,
		volume = $bindable(1),
		looped = $bindable(false),
		onplaypause,
		onprev,
		onnext
	}: {
		sample: CatalogFile;
		playing: boolean;
		currentTime: number;
		duration: number;
		volume: number;
		looped: boolean;
		onplaypause: () => void;
		onprev: () => void;
		onnext: () => void;
	} = $props();

	let title = $derived(fileStem(sample.name));
	let playLabel = $derived(playing ? 'Pause' : 'Play');
	let seekable = $derived(Number.isFinite(duration) && duration > 0);
	let seekMax = $derived(seekable ? duration : 0);
	let progressMax = $derived(seekable ? duration : 1);
	let progressValue = $derived(seekable ? currentTime : 0);
	let folderLabel = $derived(sample.parent_path.split('/').filter(Boolean).join(' ') || 'Library');
</script>

<footer
	class="shrink-0 border-t border-base-300 bg-base-100"
	transition:fly={{ y: 16, duration: 180 }}
>
	<div class="relative leading-none">
		<progress class="progress block h-1 w-full rounded-none" value={progressValue} max={progressMax}
		></progress>
		<input
			type="range"
			class="range range-xs absolute inset-0 w-full opacity-0"
			min="0"
			max={seekMax}
			step="0.01"
			disabled={!seekable}
			aria-label="Seek"
			bind:value={currentTime}
		/>
	</div>
	<div class="flex items-center gap-2 px-3 py-2">
		<div class="flex shrink-0 items-center">
			<IconButton label="Previous" onclick={onprev}>
				<span class="icon-[lucide--skip-back] size-4" aria-hidden="true"></span>
			</IconButton>
			<div class="tooltip" data-tip={playLabel}>
				<button
					type="button"
					class={['btn btn-ghost btn-square btn-sm swap', playing && 'swap-active']}
					aria-label={playLabel}
					onclick={onplaypause}
				>
					<span class="icon-[lucide--pause] swap-on size-5" aria-hidden="true"></span>
					<span class="icon-[lucide--play] swap-off size-5" aria-hidden="true"></span>
				</button>
			</div>
			<IconButton label="Next" onclick={onnext}>
				<span class="icon-[lucide--skip-forward] size-4" aria-hidden="true"></span>
			</IconButton>
		</div>

		<IconButton
			label="Loop"
			tip={looped ? 'Loop on' : 'Loop off'}
			active={looped}
			onclick={() => (looped = !looped)}
		>
			<span class="icon-[lucide--repeat] size-4" aria-hidden="true"></span>
		</IconButton>

		<div class="min-w-0 flex-1">
			<p class="truncate text-sm font-semibold">{title}</p>
			<p class="truncate text-xs opacity-50">
				{folderLabel}
				<span class="badge badge-ghost badge-xs ms-1">{formatAudioFormat(sample.format)}</span>
			</p>
		</div>

		<div class="flex shrink-0 items-center self-stretch">
			<div class="flex flex-col items-center justify-center px-2">
				<span class="text-sm font-semibold leading-none">{formatKey(sample.key)}</span>
				<span class="mt-1 text-[0.625rem] font-medium tracking-wide uppercase opacity-50">Key</span>
			</div>
			<div class="divider divider-horizontal mx-0"></div>
			<div class="flex flex-col items-center justify-center px-2">
				<span class="text-sm font-semibold leading-none tabular-nums">{formatBpm(sample.bpm)}</span>
				<span class="mt-1 text-[0.625rem] font-medium tracking-wide uppercase opacity-50">Bpm</span>
			</div>
		</div>

		<label class="flex shrink-0 items-center gap-2">
			<span class="icon-[lucide--volume-2] size-4 opacity-70" aria-hidden="true"></span>
			<input
				type="range"
				class="range range-xs w-16 sm:w-20"
				min="0"
				max="1"
				step="0.01"
				aria-label="Volume"
				bind:value={volume}
			/>
		</label>
	</div>
</footer>
