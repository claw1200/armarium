<script module lang="ts">
	let pendingSelect: 'first' | 'last' | null = null;
</script>

<script lang="ts">
	import { afterNavigate, goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { navigating } from '$app/state';
	import { audioUrl, DEFAULT_PAGE_SIZE, type CatalogFile } from '$lib/api';
	import { cacheSample, startCachedDrag } from '$lib/cache';
	import { toErrorMessage } from '$lib/error';
	import { formatDuration } from '$lib/format';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	let selectedPath = $state<string | null>(null);
	let cachePath = $state<string | null>(null);
	let cacheError = $state<string | null>(null);
	let downloading = $state(false);
	let playing = $state(false);
	let downloadGen = 0;
	let audioEl = $state<HTMLAudioElement | null>(null);

	let catalog = $derived(data.catalog);
	let items = $derived(catalog?.items ?? []);
	let total = $derived(catalog?.total ?? 0);
	let limit = $derived(catalog?.limit ?? DEFAULT_PAGE_SIZE);
	let offset = $derived(catalog?.offset ?? 0);
	let selected = $derived(items.find((file) => file.path === selectedPath) ?? null);
	let loading = $derived(navigating.to !== null);
	let pageNumber = $derived(Math.floor(offset / limit) + 1);
	let pageCount = $derived(Math.max(1, Math.ceil(total / limit)));
	let previousOffset = $derived(Math.max(0, offset - limit));
	let nextOffset = $derived(offset + limit);

	afterNavigate(() => {
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

	function selectFile(file: CatalogFile): void {
		if (file.path === selectedPath) {
			return;
		}
		selectedPath = file.path;
		cachePath = null;
		cacheError = null;
		downloading = false;
		downloadGen += 1;
	}

	function previewFile(file: CatalogFile): void {
		if (file.path === selectedPath) {
			void audioEl?.play();
			return;
		}
		selectFile(file);
		queueMicrotask(() => {
			document
				.querySelector(`[data-path="${CSS.escape(file.path)}"]`)
				?.scrollIntoView({ block: 'nearest' });
		});
	}

	function togglePlay(file: CatalogFile): void {
		if (playing && file.path === selectedPath) {
			audioEl?.pause();
			return;
		}
		previewFile(file);
	}

	async function downloadFile(file: CatalogFile): Promise<void> {
		selectFile(file);
		if (downloading) {
			return;
		}
		const path = file.path;
		const gen = ++downloadGen;
		downloading = true;
		cachePath = null;
		cacheError = null;
		try {
			const localPath = await cacheSample(path);
			if (gen !== downloadGen) {
				return;
			}
			cachePath = localPath;
		} catch (error) {
			if (gen !== downloadGen) {
				return;
			}
			cacheError = toErrorMessage(error);
		} finally {
			if (gen === downloadGen) {
				downloading = false;
			}
		}
	}

	async function dragFile(event: PointerEvent, file: CatalogFile): Promise<void> {
		event.stopPropagation();
		if (event.button !== 0) {
			return;
		}
		selectFile(file);
		if (downloading) {
			return;
		}
		const path = file.path;
		try {
			const result = await startCachedDrag(path);
			if (path !== selectedPath) {
				return;
			}
			if (result.status === 'needsDownload') {
				await downloadFile(file);
				return;
			}
			cachePath = result.path;
			cacheError = null;
		} catch (error) {
			if (path !== selectedPath) {
				return;
			}
			cacheError = toErrorMessage(error);
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
		const index = items.findIndex((file) => file.path === selectedPath);
		if (event.key === 'ArrowDown') {
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
</script>

{#snippet playIcon()}
	<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-4" aria-hidden="true">
		<path d="M8 5.14v13.72a1 1 0 0 0 1.5.86l11-6.86a1 1 0 0 0 0-1.72l-11-6.86a1 1 0 0 0-1.5.86Z" />
	</svg>
{/snippet}

{#snippet pauseIcon()}
	<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-4" aria-hidden="true">
		<path d="M6 5h4v14H6zm8 0h4v14h-4z" />
	</svg>
{/snippet}

{#snippet downloadIcon()}
	<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-4" aria-hidden="true">
		<path
			d="M12 3a1 1 0 0 1 1 1v9.59l3.3-3.3a1 1 0 1 1 1.4 1.42l-5 5a1 1 0 0 1-1.4 0l-5-5a1 1 0 1 1 1.4-1.42L11 13.59V4a1 1 0 0 1 1-1m-7 15a1 1 0 0 1 1 1v1h12v-1a1 1 0 1 1 2 0v1a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1a1 1 0 0 1 1-1"
		/>
	</svg>
{/snippet}

{#snippet dragIcon()}
	<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-4" aria-hidden="true">
		<path
			d="M9 5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m9 0a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0M9 12a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m9 0a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0M9 19a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m9 0a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"
		/>
	</svg>
{/snippet}

<svelte:head>
	<title>Armarium</title>
</svelte:head>

<svelte:window onkeydown={onWindowKeydown} />

<div class="flex min-h-screen flex-col">
	<div class="navbar bg-base-200">
		<div class="navbar-start">
			<span class="px-2 text-lg font-semibold">Armarium</span>
		</div>
		<div class="navbar-center">
			<span class="flex items-center gap-2 text-sm">
				<kbd class="kbd kbd-sm">↑</kbd>
				<kbd class="kbd kbd-sm">↓</kbd>
				<span>preview</span>
			</span>
		</div>
		<div class="navbar-end px-4">
			{#if loading}
				<span class="loading loading-spinner" aria-label="Loading"></span>
			{/if}
		</div>
	</div>

	<main class="flex flex-1 flex-col gap-4 p-4">
		{#if data.loadError}
			<div role="alert" class="alert alert-error">{data.loadError}</div>
		{/if}
		{#if cacheError}
			<div role="alert" class="alert alert-error">{cacheError}</div>
		{/if}

		{#if catalog}
			{#if items.length === 0}
				<p>No samples in the library.</p>
			{:else}
				<div class="overflow-x-auto">
					<table class="table table-pin-rows">
						<thead>
							<tr>
								<th></th>
								<th>Filename</th>
								<th>Time</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							{#each items as file (file.path)}
								<tr
									data-path={file.path}
									class={['cursor-pointer hover:bg-base-200', selectedPath === file.path && 'bg-base-200']}
									onclick={() => previewFile(file)}
								>
									<td class="w-12">
										<div
											class="tooltip"
											data-tip={playing && file.path === selectedPath ? 'Pause' : 'Play'}
										>
											<button
												type="button"
												class={[
													'btn btn-ghost btn-sm btn-square',
													playing && file.path === selectedPath && 'btn-active'
												]}
												aria-label={playing && file.path === selectedPath ? 'Pause' : 'Play'}
												onclick={(event) => {
													event.stopPropagation();
													togglePlay(file);
												}}
											>
												{#if playing && file.path === selectedPath}
													{@render pauseIcon()}
												{:else}
													{@render playIcon()}
												{/if}
											</button>
										</div>
									</td>
									<td>
										<div class="flex min-w-0 flex-col">
											<span class="truncate">{file.name}</span>
											{#if file.parent_path}
												<span class="truncate text-sm opacity-70">{file.parent_path}</span>
											{/if}
										</div>
									</td>
									<td class="whitespace-nowrap">{formatDuration(file.duration_seconds)}</td>
									<td>
										<div class="flex items-center gap-1">
											<div class="tooltip" data-tip="Download">
												<button
													type="button"
													class="btn btn-ghost btn-sm btn-square"
													aria-label="Download"
													disabled={downloading}
													onclick={(event) => {
														event.stopPropagation();
														void downloadFile(file);
													}}
												>
													{#if downloading && file.path === selectedPath}
														<span class="loading loading-spinner" aria-label="Downloading"></span>
													{:else}
														{@render downloadIcon()}
													{/if}
												</button>
											</div>
											<div class="tooltip" data-tip="Drag">
												<button
													type="button"
													class="btn btn-ghost btn-sm btn-square cursor-grab"
													aria-label="Drag"
													disabled={downloading}
													onpointerdown={(event) => void dragFile(event, file)}
												>
													{@render dragIcon()}
												</button>
											</div>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}

			{#if total > limit}
				<div class="join">
					{#if offset > 0}
						<a class="btn join-item" href={resolve(filesHref(previousOffset))}>Previous</a>
					{:else}
						<button type="button" class="btn join-item" disabled>Previous</button>
					{/if}
					<button type="button" class="btn join-item" disabled>{pageNumber} / {pageCount}</button>
					{#if nextOffset < total}
						<a class="btn join-item" href={resolve(filesHref(nextOffset))}>Next</a>
					{:else}
						<button type="button" class="btn join-item" disabled>Next</button>
					{/if}
				</div>
			{/if}
		{/if}
		{#if cachePath}
			<p class="truncate text-sm opacity-70">{cachePath}</p>
		{/if}
	</main>
</div>

{#if selected}
	{#key selected.path}
		<audio
			bind:this={audioEl}
			hidden
			autoplay
			src={audioUrl(selected.path)}
			onplay={() => (playing = true)}
			onpause={() => (playing = false)}
			onended={() => (playing = false)}
		></audio>
	{/key}
{/if}
