<script lang="ts">
	import { favouriteFolders, sidebarTags } from '$lib/placeholders';

	let { drawerOpen = $bindable(false) }: { drawerOpen?: boolean } = $props();

	let selectedFavourite = $state(favouriteFolders[0]?.id ?? 'all');
	let selectedTag = $state<string | null>(null);

	const sidebarLabelClass =
		'min-w-0 flex-1 overflow-x-clip whitespace-nowrap text-start is-drawer-close:hidden';

	function isOverlayDrawerMode(): boolean {
		return window.matchMedia('(max-width: 639px)').matches;
	}

	function handleNavClick() {
		if (isOverlayDrawerMode() && drawerOpen) {
			drawerOpen = false;
		}
	}

	function onSubmenuSummaryClick(event: MouseEvent) {
		if (drawerOpen) return;
		event.preventDefault();
		drawerOpen = true;
		const details = (event.currentTarget as HTMLElement).closest('details');
		if (details) details.open = true;
	}

	function selectFavourite(id: string): void {
		selectedFavourite = id;
		handleNavClick();
	}

	function selectTag(id: string): void {
		selectedTag = selectedTag === id ? null : id;
		handleNavClick();
	}
</script>

<div
	class="flex min-h-full min-w-0 flex-col items-start overflow-x-clip border-r border-base-300 bg-base-100 transition-[width] duration-300 ease-out is-drawer-close:w-14 is-drawer-close:overflow-visible is-drawer-open:w-64"
>
	<div class="navbar min-h-16 w-full min-w-0 is-drawer-close:px-0 is-drawer-open:px-2">
		<div
			class="flex w-full min-w-0 items-center is-drawer-close:justify-center is-drawer-close:overflow-visible is-drawer-open:gap-2 is-drawer-open:overflow-x-clip is-drawer-open:px-2"
		>
			<span class="icon-[lucide--music] size-6 shrink-0" aria-hidden="true"></span>
			<span class="font-semibold {sidebarLabelClass}">Armarium</span>
		</div>
	</div>
	<ul class="menu min-w-0 w-full grow">
		<li class="min-w-0">
			<details class="min-w-0" open>
				<summary
					class="min-w-0 cursor-pointer select-none is-drawer-close:after:hidden"
					onclick={onSubmenuSummaryClick}
				>
					<span class="icon-[lucide--star] my-1.5 size-4 shrink-0" aria-hidden="true"></span>
					<span class={sidebarLabelClass}>Favourites</span>
				</summary>
				<ul class="min-w-0 is-drawer-close:hidden">
					{#each favouriteFolders as folder (folder.id)}
						<li class="min-w-0">
							<button
								type="button"
								class="min-w-0"
								class:menu-active={selectedFavourite === folder.id}
								aria-label={folder.label}
								onclick={() => selectFavourite(folder.id)}
							>
								<span
									class={[
										'my-1.5 size-4 shrink-0',
										folder.id === 'all' ? 'icon-[lucide--music]' : 'icon-[lucide--folder]'
									]}
									aria-hidden="true"
								></span>
								<span class={sidebarLabelClass}>{folder.label}</span>
							</button>
						</li>
					{/each}
				</ul>
			</details>
		</li>
		<li class="min-w-0">
			<details class="min-w-0" open>
				<summary
					class="min-w-0 cursor-pointer select-none is-drawer-close:after:hidden"
					onclick={onSubmenuSummaryClick}
				>
					<span class="icon-[lucide--tags] my-1.5 size-4 shrink-0" aria-hidden="true"></span>
					<span class={sidebarLabelClass}>Tags</span>
				</summary>
				<ul class="min-w-0 is-drawer-close:hidden">
					{#each sidebarTags as tag (tag.id)}
						<li class="min-w-0">
							<button
								type="button"
								class="min-w-0"
								class:menu-active={selectedTag === tag.id}
								aria-label={tag.label}
								onclick={() => selectTag(tag.id)}
							>
								<span class="icon-[lucide--tag] my-1.5 size-4 shrink-0" aria-hidden="true"></span>
								<span class={sidebarLabelClass}>{tag.label}</span>
							</button>
						</li>
					{/each}
				</ul>
			</details>
		</li>
	</ul>
</div>
