<script lang="ts">
	import type { Snippet } from 'svelte';
	import LibrarySidebar from './LibrarySidebar.svelte';
	import SearchBar from './SearchBar.svelte';

	const drawerId = 'library-drawer';

	let {
		q = '',
		loading = false,
		onquery,
		onsearch,
		children,
		footer
	}: {
		q?: string;
		loading?: boolean;
		onquery?: (q: string) => void;
		onsearch?: (q: string) => void;
		children: Snippet;
		footer?: Snippet;
	} = $props();

	let drawerOpen = $state(true);
</script>

<div class="drawer sm:drawer-open h-dvh">
	<input id={drawerId} type="checkbox" class="drawer-toggle" bind:checked={drawerOpen} />
	<div class="drawer-content flex min-h-0 flex-col overflow-hidden bg-base-200">
		<nav class="navbar min-h-12 shrink-0 gap-2 border-b border-base-300 bg-base-100 px-3">
			<div class="navbar-start w-auto shrink-0">
				<label for={drawerId} class="btn btn-square btn-ghost" aria-label="Toggle sidebar">
					<span class="icon-[lucide--panel-left-open] size-5" aria-hidden="true"></span>
				</label>
			</div>
			<div class="navbar-center min-w-0 flex-1">
				<SearchBar value={q} {loading} {onquery} {onsearch} />
			</div>
			<div class="navbar-end w-auto shrink-0">
				<span class="hidden items-center gap-1 text-xs opacity-70 sm:flex">
					<kbd class="kbd kbd-sm">↑</kbd>
					<kbd class="kbd kbd-sm">↓</kbd>
				</span>
			</div>
		</nav>
		<div class="page-content flex min-h-0 flex-1 flex-col overflow-hidden">
			{@render children()}
		</div>
		{#if footer}
			{@render footer()}
		{/if}
	</div>
	<div class="drawer-side is-drawer-close:overflow-visible z-20">
		<label for={drawerId} class="drawer-overlay" aria-label="Close sidebar"></label>
		<LibrarySidebar bind:drawerOpen />
	</div>
</div>
