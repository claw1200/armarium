<script lang="ts">
	import { favouriteFolders, sidebarTags } from '$lib/placeholders';
	import Icon from './Icon.svelte';

	let selectedFavourite = $state(favouriteFolders[0]?.id ?? 'all');
	let selectedTag = $state<string | null>(null);

	function selectFavourite(id: string): void {
		selectedFavourite = id;
	}

	function selectTag(id: string): void {
		selectedTag = selectedTag === id ? null : id;
	}
</script>

<aside class="flex h-full min-h-full w-44 flex-col bg-base-200">
	<div class="px-4 py-3 text-lg font-semibold">Armarium</div>
	<nav class="min-h-0 flex-1 overflow-y-auto">
		<ul class="menu menu-sm w-full">
			<li>
				<details open>
					<summary>Favourites</summary>
					<ul>
						{#each favouriteFolders as folder (folder.id)}
							<li>
								<button
									type="button"
									class={{ 'menu-active': selectedFavourite === folder.id }}
									onclick={() => selectFavourite(folder.id)}
								>
									<Icon name={folder.id === 'all' ? 'music' : 'folder'} />
									{folder.label}
								</button>
							</li>
						{/each}
					</ul>
				</details>
			</li>
			<li>
				<details open>
					<summary>Tags</summary>
					<ul>
						{#each sidebarTags as tag (tag.id)}
							<li>
								<button
									type="button"
									class={{ 'menu-active': selectedTag === tag.id }}
									onclick={() => selectTag(tag.id)}
								>
									<Icon name="tag" />
									{tag.label}
								</button>
							</li>
						{/each}
					</ul>
				</details>
			</li>
		</ul>
	</nav>
</aside>
