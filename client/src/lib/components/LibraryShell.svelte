<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from './Icon.svelte';
	import LibrarySidebar from './LibrarySidebar.svelte';
	import SearchBar from './SearchBar.svelte';

	let {
		q = '',
		loading = false,
		onquery,
		onsearch,
		children
	}: {
		q?: string;
		loading?: boolean;
		onquery?: (q: string) => void;
		onsearch?: (q: string) => void;
		children: Snippet;
	} = $props();
</script>

<div class="drawer sm:drawer-open h-dvh">
	<input id="library-drawer" type="checkbox" class="drawer-toggle" />
	<div class="drawer-content flex min-h-0 flex-col overflow-hidden">
		<div class="navbar min-h-12 shrink-0 gap-2 bg-base-200 px-3">
			<div class="navbar-start w-auto shrink-0">
				<label for="library-drawer" class="btn btn-ghost btn-square btn-sm sm:hidden" aria-label="Open sidebar">
					<Icon name="menu" />
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
		</div>
		<div class="flex min-h-0 flex-1 flex-col overflow-hidden">
			{@render children()}
		</div>
	</div>
	<div class="drawer-side z-20">
		<label for="library-drawer" class="drawer-overlay" aria-label="Close sidebar"></label>
		<LibrarySidebar />
	</div>
</div>
