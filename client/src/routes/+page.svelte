<script lang="ts">
	import { resolve } from '$app/paths';
	import { navigating, page } from '$app/state';
	import { audioUrl, type CatalogFile } from '$lib/api';
	import { cacheSample } from '$lib/cache';
	import { breadcrumbs, folderHref } from '$lib/catalog-path';
	import { toErrorMessage } from '$lib/error';
	import { formatDuration, formatSize } from '$lib/format';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	let selectedPath = $state<string | null>(null);
	let cachePath = $state<string | null>(null);
	let cacheError = $state<string | null>(null);
	let downloading = $state(false);
	let downloadGen = 0;

	let listing = $derived(data.listing);
	let crumbs = $derived(breadcrumbs(listing?.path ?? page.url.searchParams.get('path') ?? ''));
	let selected = $derived(listing?.files.find((file) => file.path === selectedPath) ?? null);
	let loading = $derived(navigating.to !== null);

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

	async function downloadSelected(): Promise<void> {
		if (!selected || downloading) {
			return;
		}
		const path = selected.path;
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
</script>

<svelte:head>
	<title>Armarium</title>
</svelte:head>

<div class="flex min-h-screen flex-col">
	<div class="navbar bg-base-200">
		<div class="navbar-start">
			<span class="px-2 text-lg font-semibold">Armarium</span>
		</div>
		{#if loading}
			<div class="navbar-end px-4">
				<span class="loading loading-spinner" aria-label="Loading folder"></span>
			</div>
		{/if}
	</div>

	<main class="flex flex-1 flex-col gap-4 p-4">
		<div class="breadcrumbs text-sm">
			<ul>
				{#each crumbs as crumb, index (crumb.path || 'root')}
					<li>
						{#if index < crumbs.length - 1}
							<a href={resolve(folderHref(crumb.path))}>{crumb.name}</a>
						{:else}
							{crumb.name}
						{/if}
					</li>
				{/each}
			</ul>
		</div>

		{#if data.loadError}
			<div role="alert" class="alert alert-error">{data.loadError}</div>
		{:else if listing}
			{#if listing.folders.length === 0 && listing.files.length === 0}
				<p>This folder is empty.</p>
			{:else}
				<ul class="list">
					{#each listing.folders as folder (folder.path)}
						<li class="list-row">
							<a class="btn list-col-grow justify-start" href={resolve(folderHref(folder.path))}>
								{folder.name}
							</a>
						</li>
					{/each}
					{#each listing.files as file (file.path)}
						<li class="list-row">
							<button
								type="button"
								class={[
									'btn',
									'list-col-grow',
									'justify-start',
									selectedPath === file.path && 'btn-active'
								]}
								aria-pressed={selectedPath === file.path}
								onclick={() => selectFile(file)}
							>
								<span class="truncate">{file.name}</span>
								<span class="text-sm opacity-70">
									{file.format}
									{formatDuration(file.duration_seconds)}
									{formatSize(file.size_bytes)}
								</span>
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		{/if}
	</main>

	{#if selected}
		<div class="border-t border-base-300 bg-base-200 p-4">
			<p class="mb-2 truncate">{selected.name}</p>
			{#key selected.path}
				<audio class="w-full" controls autoplay src={audioUrl(selected.path)}></audio>
			{/key}
			<div class="mt-2 flex items-center gap-2">
				<button type="button" class="btn" disabled={downloading} onclick={downloadSelected}>
					Download
				</button>
				{#if downloading}
					<span class="loading loading-spinner" aria-label="Downloading"></span>
				{/if}
			</div>
			{#if cachePath}
				<p class="mt-2 truncate">{cachePath}</p>
			{/if}
			{#if cacheError}
				<div role="alert" class="alert alert-error mt-2">{cacheError}</div>
			{/if}
		</div>
	{/if}
</div>
