<script lang="ts">
	import { afterNavigate, goto, invalidateAll } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { navigating } from '$app/state';
	import { audioUrl, fetchFiles, type CatalogFile, type CatalogPage } from '$lib/api';
	import { cacheSample, listCached, startCachedDrag } from '$lib/cache';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ErrorBanner from '$lib/components/ErrorBanner.svelte';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import LibraryShell from '$lib/components/LibraryShell.svelte';
	import SampleList from '$lib/components/SampleList.svelte';
	import SamplePlayer from '$lib/components/SamplePlayer.svelte';
	import { toErrorMessage } from '$lib/error';
	import { scanWatch } from '$lib/scan';
	import type { Attachment } from 'svelte/attachments';
	import { SvelteSet, SvelteURLSearchParams } from 'svelte/reactivity';

	const dragThresholdPx = 6;
	const searchDebounceMs = 300;
	const loadMoreMarginPx = 240;

	let { data }: { data: { catalog: CatalogPage | null; q: string; loadError: string | null } } =
		$props();
	let selectedPath = $state<string | null>(null);
	let cached = new SvelteSet<string>();
	let cacheError = $state<string | null>(null);
	let moreError = $state<string | null>(null);
	let extraItems = $state.raw<CatalogFile[]>([]);
	let loadingMore = $state(false);
	let downloadingPath = $state<string | null>(null);
	let paused = $state(true);
	let currentTime = $state(0);
	let duration = $state(Number.NaN);
	let volume = $state(1);
	let looped = $state(false);
	let searchTimer: ReturnType<typeof setTimeout> | undefined;
	let listScroller: HTMLDivElement | null = null;
	let downloadGen = 0;
	let cachedListGen = 0;
	let moreGen = 0;
	let pendingDrag: { path: string; x: number; y: number } | null = null;
	let skipRowClick = false;

	let catalog = $derived(data.catalog);
	let items = $derived([...(catalog?.items ?? []), ...extraItems]);
	let total = $derived(catalog?.total ?? 0);
	let selected = $derived(items.find((file) => file.path === selectedPath) ?? null);
	let loading = $derived(navigating.to !== null);
	let hasMore = $derived(items.length < total);
	let playing = $derived(!paused);
	let playingPath = $derived(playing ? selectedPath : null);
	let resultLabel = $derived(
		catalog ? `${total.toLocaleString()} ${total === 1 ? 'result' : 'results'}` : ''
	);

	afterNavigate(() => {
		listScroller?.scrollTo(0, 0);
		moreGen += 1;
		extraItems = [];
		loadingMore = false;
		moreError = null;
		void refreshCached(
			(data.catalog?.items ?? []).map((file) => file.path),
			true
		);
	});

	$effect(() => {
		return scanWatch.onComplete(refreshAfterScan);
	});

	function refreshAfterScan(): void {
		moreGen += 1;
		extraItems = [];
		void invalidateAll();
	}

	function filesHref(query = data.q): '/' | `/?${string}` {
		const trimmed = query.trim();
		if (!trimmed) {
			return '/';
		}
		const params = new SvelteURLSearchParams();
		params.set('q', trimmed);
		return `/?${params.toString()}`;
	}

	function applySearch(raw: string): void {
		const next = raw.trim();
		if (next === data.q) {
			return;
		}
		void goto(resolve(filesHref(next)), { keepFocus: true, noScroll: true, replaceState: true });
	}

	function onSearchInput(raw: string): void {
		clearTimeout(searchTimer);
		searchTimer = setTimeout(() => applySearch(raw), searchDebounceMs);
	}

	function onSearchSubmit(raw: string): void {
		clearTimeout(searchTimer);
		applySearch(raw);
	}

	function isTypingTarget(target: EventTarget | null): boolean {
		if (!(target instanceof HTMLElement)) {
			return false;
		}
		const tag = target.tagName;
		return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable;
	}

	function refreshCached(paths: string[], replace: boolean): Promise<void> {
		const gen = ++cachedListGen;
		return listCached(paths)
			.then((hits) => {
				if (gen !== cachedListGen) {
					return;
				}
				if (replace) {
					cached.clear();
				}
				for (const hit of hits) {
					cached.add(hit);
				}
			})
			.catch(() => {
				if (gen === cachedListGen && replace) {
					cached.clear();
				}
			});
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

	function onRowPreview(file: CatalogFile): void {
		if (skipRowClick) {
			skipRowClick = false;
			return;
		}
		previewFile(file);
	}

	function onRowPointerDown(event: PointerEvent, file: CatalogFile): void {
		skipRowClick = false;
		if (event.button !== 0 || !cached.has(file.path)) {
			return;
		}
		pendingDrag = { path: file.path, x: event.clientX, y: event.clientY };
	}

	function onWindowPointerMove(event: PointerEvent): void {
		if (pendingDrag === null) {
			return;
		}
		if (event.buttons !== 1) {
			pendingDrag = null;
			return;
		}
		const dx = event.clientX - pendingDrag.x;
		const dy = event.clientY - pendingDrag.y;
		if (dx * dx + dy * dy < dragThresholdPx * dragThresholdPx) {
			return;
		}
		event.preventDefault();
		const path = pendingDrag.path;
		pendingDrag = null;
		skipRowClick = true;
		void beginCachedDrag(path);
	}

	function clearPendingDrag(): void {
		pendingDrag = null;
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

	function sentinelVisible(node: HTMLElement): boolean {
		const root = node.parentElement;
		if (!root) {
			return false;
		}
		return node.getBoundingClientRect().top < root.getBoundingClientRect().bottom + loadMoreMarginPx;
	}

	async function loadMore(): Promise<boolean> {
		if (loadingMore || !catalog || items.length >= catalog.total) {
			return false;
		}
		const gen = moreGen;
		const offset = items.length;
		loadingMore = true;
		moreError = null;
		try {
			const page = await fetchFiles({
				offset,
				limit: catalog.limit,
				q: data.q || undefined
			});
			if (gen !== moreGen) {
				return false;
			}
			if (page.items.length === 0) {
				return false;
			}
			extraItems = [...extraItems, ...page.items];
			void refreshCached(
				page.items.map((file) => file.path),
				false
			);
			return true;
		} catch (error) {
			if (gen === moreGen) {
				moreError = toErrorMessage(error);
			}
			return false;
		} finally {
			if (gen === moreGen) {
				loadingMore = false;
			}
		}
	}

	const bindScroller: Attachment<HTMLDivElement> = (node) => {
		listScroller = node;
		return () => {
			if (listScroller === node) {
				listScroller = null;
			}
		};
	};

	const watchVisible: Attachment<HTMLElement> = (node) => {
		const root = node.parentElement;
		const observer = new IntersectionObserver(
			(entries) => {
				if (!entries.some((entry) => entry.isIntersecting)) {
					return;
				}
				void loadMore().then((loaded) => {
					if (loaded && sentinelVisible(node)) {
						void loadMore();
					}
				});
			},
			{ root, rootMargin: `${loadMoreMarginPx}px` }
		);
		observer.observe(node);
		return () => observer.disconnect();
	};

	async function skipSample(delta: -1 | 1): Promise<void> {
		if (items.length === 0) {
			return;
		}
		const index = items.findIndex((file) => file.path === selectedPath);
		if (delta > 0) {
			const nextIndex = index < 0 ? 0 : index + 1;
			if (nextIndex >= items.length && hasMore) {
				await loadMore();
			}
			const nextFile = items[nextIndex];
			if (nextFile !== undefined) {
				previewFile(nextFile);
			}
			return;
		}
		const previousFile = index < 0 ? items.at(-1) : items[index - 1];
		if (previousFile) {
			previewFile(previousFile);
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
		void skipSample(event.key === 'ArrowDown' ? 1 : -1);
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

<LibraryShell q={data.q} {loading} onquery={onSearchInput} onsearch={onSearchSubmit}>
	<main class="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden p-3">
		{#if data.loadError}
			<ErrorBanner kind="error" text={data.loadError} />
		{/if}
		{#if cacheError}
			<ErrorBanner kind="error" text={cacheError} onDismiss={() => (cacheError = null)} />
		{/if}
		{#if moreError}
			<ErrorBanner kind="error" text={moreError} onDismiss={() => (moreError = null)} />
		{/if}

		{#if catalog}
			<FilterBar {resultLabel} />
		{/if}

		<div
			class="card flex min-h-0 flex-1 flex-col overflow-hidden bg-base-100"
			aria-busy={loading}
		>
			{#if !catalog}
				{#if data.loadError}
					<EmptyState text="Couldn't load the library." />
				{:else}
					<div class="flex justify-center py-16">
						<span
							class="icon-[lucide--loader-circle] size-10 animate-spin text-primary"
							aria-label="Loading library"
						></span>
					</div>
				{/if}
			{:else}
				<div class="min-h-0 flex-1 overflow-y-auto" {@attach bindScroller}>
					<SampleList
						{items}
						{selectedPath}
						{playingPath}
						{cached}
						{downloadingPath}
						onpreview={onRowPreview}
						ontogglePlay={togglePlay}
						ondownload={downloadFile}
						onpointerdown={onRowPointerDown}
						onstopGesture={stopRowGesture}
					/>
					{#if hasMore}
						<div class="flex justify-center py-4" {@attach watchVisible}>
							<span
								class={['loading loading-spinner', !loadingMore && 'invisible']}
								aria-hidden={!loadingMore}
								aria-label="Loading more samples"
							></span>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</main>
	{#snippet footer()}
		{#if selected}
			<SamplePlayer
				sample={selected}
				{playing}
				bind:currentTime
				{duration}
				bind:volume
				bind:looped
				onplaypause={() => togglePlay(selected)}
				onprev={() => void skipSample(-1)}
				onnext={() => void skipSample(1)}
			/>
		{/if}
	{/snippet}
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
