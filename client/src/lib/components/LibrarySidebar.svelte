<script lang="ts">
	import { LOCATIONS, type LocationId } from '$lib/locations';
	import { FACET_LABELS, FACET_ORDER, TAGS_BY_FACET, tagForFacet, type TagFacet } from '$lib/tags';

	let {
		drawerOpen = $bindable(false),
		location = 'all',
		tags = [],
		onlocation,
		onfacet
	}: {
		drawerOpen?: boolean;
		location?: LocationId;
		tags?: string[];
		onlocation?: (location: LocationId) => void;
		onfacet?: (facet: TagFacet, slug: string) => void;
	} = $props();

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

	function selectLocation(id: LocationId): void {
		onlocation?.(id);
		handleNavClick();
	}

	function selectTag(facet: TagFacet, slug: string): void {
		onfacet?.(facet, tagForFacet(tags, facet) === slug ? '' : slug);
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
					<span class="icon-[lucide--map-pin] my-1.5 size-4 shrink-0" aria-hidden="true"></span>
					<span class={sidebarLabelClass}>Locations</span>
				</summary>
				<ul class="min-w-0 is-drawer-close:hidden">
					{#each LOCATIONS as item (item.id)}
						{@const selected = location === item.id}
						<li class="min-w-0">
							<button
								type="button"
								class={['min-w-0', selected && 'menu-active']}
								aria-label={item.label}
								aria-pressed={selected}
								onclick={() => selectLocation(item.id)}
							>
								<span class={['my-1.5 size-4 shrink-0', item.icon]} aria-hidden="true"></span>
								<span class={sidebarLabelClass}>{item.label}</span>
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
					{#each FACET_ORDER as facet (facet)}
						<li class="menu-title">{FACET_LABELS[facet]}</li>
						{#each TAGS_BY_FACET[facet] as tag (tag)}
							{@const selected = tagForFacet(tags, facet) === tag}
							<li class="min-w-0">
								<button
									type="button"
									class={['min-w-0', selected && 'menu-active']}
									aria-label={tag}
									aria-pressed={selected}
									onclick={() => selectTag(facet, tag)}
								>
									<span class="icon-[lucide--tag] my-1.5 size-4 shrink-0" aria-hidden="true"></span>
									<span class={sidebarLabelClass}>{tag}</span>
								</button>
							</li>
						{/each}
					{/each}
				</ul>
			</details>
		</li>
	</ul>
</div>
