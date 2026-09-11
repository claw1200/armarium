<script lang="ts">
	import LibraryPage from '$lib/pages/LibraryPage.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<LibraryPage {data} />
