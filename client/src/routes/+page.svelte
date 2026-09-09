<script module lang="ts">
	let pendingSelect: 'first' | 'last' | null = null;
</script>

<script lang="ts">
	import { afterNavigate, goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { navigating } from '$app/state';
	import { audioUrl, DEFAULT_PAGE_SIZE, type CatalogFile } from '$lib/api';
	import { cacheSample, listCached, startCachedDrag } from '$lib/cache';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import LibraryShell from '$lib/components/LibraryShell.svelte';
	import SampleList from '$lib/components/SampleList.svelte';
	import SamplePager from '$lib/components/SamplePager.svelte';
	import SamplePlayer from '$lib/components/SamplePlayer.svelte';
	import { toErrorMessage } from '$lib/error';
	import { SvelteSet } from 'svelte/reactivity';
	import type { PageProps } from './$types';

	const dragThresholdPx = 6;

	let { data }: PageProps = $props();
	let selectedPath = $state<string | null>(null);
	let cached = new SvelteSet<string>();
	let cacheError = $state<string | null>(null);
	let downloadingPath = $state<string | null>(null);
	let paused = $state(true);
	let currentTime = $state(0);
	let duration = $state(Number.NaN);
	let volume = $state(1);
	let looped = $state(false);
	let search = $state('');
	let downloadGen = 0;
	let cachedListGen = 0;
	let pendingDrag: { path: string; x: number; y: number } | null = null;

	let catalog = $derived(data.catalog);
	let items = $derived(catalog?.items ?? []);
	let total = $derived(catalog?.total ?? 0);
	let limit = $derived(catalog?.limit ?? DEFAULT_PAGE_SIZE);
	let offset = $derived(catalog?.offset ?? 0);
	let selected = $derived(items.find((file) => file.path === selectedPath) ?? null);
	let loading = $derived(navigating.to !== null);
	let pageCount = $derived(Math.max(1, Math.ceil(total / limit)));
	let pageNumber = $derived(Math.min(pageCount, Math.floor(offset / limit) + 1));
	let previousOffset = $derived(Math.max(0, offset - limit));
	let nextOffset = $derived(offset + limit);
	let playing = $derived(!paused);
	let playingPath = $derived(playing ? selectedPath : null);
	let resultLabel = $derived(
		catalog ? `${total.toLocaleString()} ${total === 1 ? 'result' : 'results'}` : ''
	);

	afterNavigate(() => {
		const gen = ++cachedListGen;
		const paths = items.map((file) => file.path);
		void listCached(paths)
			.then((hits) => {
				if (gen !== cachedListGen) {
					return;
				}
				cached.clear();
				for (const hit of hits) {
					cached.add(hit);
				}
			})
			.catch(() => {
				if (gen === cachedListGen) {
					cached.clear();
				}
			});
		if (pendingSelect === null) {
			return;
		}
		const file = pendingSelect === 'first' ? items[0] : items.at(-1);
		pendingSelect = null;
		if (file) {
			previewFile(file);
		}
	});

	function filesHref(targetOffset: number): '/' | `/?${string}` {
		if (targetOffset <= 0) {
			return '/';
		}
		return `/?offset=${targetOffset}`;
	}

	function isTypingTarget(target: EventTarget | null): boolean {
		if (!(target instanceof HTMLElement)) {
			return false;
		}
		const tag = target.tagName;
		return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable;
	}

	function markCached(path: string): void {
		cached.add(path);
	}

	function dropCached(path: string): void {
		cached.delete(path);
	}

	function selectFile(file: CatalogFile): void {
		if (file.path === selectedPath) {
			return;
		}
		selectedPath = file.path;
		currentTime = 0;
	}

	function previewFile(file: CatalogFile): void {
		if (file.path === selectedPath) {
			paused = false;
			return;
		}
		selectFile(file);
		queueMicrotask(() => {
			const row = document.querySelector<HTMLElement>(`[data-path="${CSS.escape(file.path)}"]`);
			row?.scrollIntoView({ block: 'nearest' });
			row?.focus({ preventScroll: true });
		});
	}

	function togglePlay(file: CatalogFile): void {
		if (!paused && file.path === selectedPath) {
			paused = true;
			return;
		}
		previewFile(file);
	}

	function stopRowGesture(event: Event): void {
		event.stopPropagation();
	}

	async function downloadFile(file: CatalogFile): Promise<void> {
		if (downloadingPath !== null) {
			return;
		}
		const path = file.path;
		const gen = ++downloadGen;
		downloadingPath = path;
		cacheError = null;
		try {
			await cacheSample(path);
			markCached(path);
		} catch (error) {
			if (gen !== downloadGen) {
				return;
			}
			cacheError = toErrorMessage(error);
		} finally {
			if (gen === downloadGen) {
				downloadingPath = null;
			}
		}
	}

	function onRowPointerDown(event: PointerEvent, file: CatalogFile): void {
		if (event.button !== 0 || !cached.has(file.path)) {
			return;
		}
		pendingDrag = { path: file.path, x: event.clientX, y: event.clientY };
	}

	function onWindowPointerMove(event: PointerEvent): void {
		if (pendingDrag === null) {
			return;
		}
		const dx = event.clientX - pendingDrag.x;
		const dy = event.clientY - pendingDrag.y;
		if (dx * dx + dy * dy < dragThresholdPx * dragThresholdPx) {
			return;
		}
		const path = pendingDrag.path;
		pendingDrag = null;
		void beginCachedDrag(path);
	}

	function clearPendingDrag(): void {
		pendingDrag = null;
	}

	async function beginCachedDrag(path: string): Promise<void> {
		try {
			const result = await startCachedDrag(path);
			if (result.status === 'needsDownload') {
				dropCached(path);
				return;
			}
			cacheError = null;
		} catch (error) {
			cacheError = toErrorMessage(error);
		}
	}

	function skipSample(delta: -1 | 1): void {
		if (items.length === 0) {
			return;
		}
		const index = items.findIndex((file) => file.path === selectedPath);
		if (delta > 0) {
			const nextFile = index < 0 ? items[0] : items[index + 1];
			if (nextFile) {
				previewFile(nextFile);
				return;
			}
			if (nextOffset < total) {
				pendingSelect = 'first';
				void goto(resolve(filesHref(nextOffset)), { keepFocus: true, noScroll: true });
			}
			return;
		}
		const previousFile = index < 0 ? items.at(-1) : items[index - 1];
		if (previousFile) {
			previewFile(previousFile);
			return;
		}
		if (offset > 0) {
			pendingSelect = 'last';
			void goto(resolve(filesHref(previousOffset)), { keepFocus: true, noScroll: true });
		}
	}

	function onWindowKeydown(event: KeyboardEvent): void {
		if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') {
			return;
		}
		if (isTypingTarget(event.target) || items.length === 0) {
			return;
		}
		event.preventDefault();
		skipSample(event.key === 'ArrowDown' ? 1 : -1);
	}
</script>

<svelte:head>
	<title>Armarium</title>
</svelte:head>

<svelte:window
	onkeydown={onWindowKeydown}
	onpointermove={onWindowPointerMove}
	onpointerup={clearPendingDrag}
	onpointercancel={clearPendingDrag}
/>

<LibraryShell bind:search {loading}>
	<main class="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden p-3">
		{#if data.loadError}
			<div role="alert" class="alert alert-error">{data.loadError}</div>
		{/if}
		{#if cacheError}
			<div role="alert" class="alert alert-error">{cacheError}</div>
		{/if}

		{#if catalog}
			<FilterBar {resultLabel} />
			<div class="min-h-0 flex-1 overflow-y-auto">
				<SampleList
					{items}
					{selectedPath}
					{playingPath}
					{cached}
					{downloadingPath}
					onpreview={previewFile}
					ontogglePlay={togglePlay}
					ondownload={downloadFile}
					onpointerdown={onRowPointerDown}
					onstopGesture={stopRowGesture}
				/>
			</div>
			{#if total > limit || offset > 0}
				<SamplePager
					{pageNumber}
					{pageCount}
					previousHref={filesHref(previousOffset)}
					nextHref={filesHref(nextOffset)}
					hasPrevious={offset > 0}
					hasNext={nextOffset < total}
				/>
			{/if}
		{/if}
	</main>
	{#if selected}
		<SamplePlayer
			sample={selected}
			{playing}
			bind:currentTime
			{duration}
			bind:volume
			bind:looped
			onplaypause={() => togglePlay(selected)}
			onprev={() => skipSample(-1)}
			onnext={() => skipSample(1)}
		/>
	{/if}
</LibraryShell>

{#if selected}
	{#key selected.path}
		<audio
			bind:currentTime
			bind:duration
			bind:volume
			bind:paused
			hidden
			autoplay
			loop={looped}
			src={audioUrl(selected.path)}
		></audio>
	{/key}
{/if}
