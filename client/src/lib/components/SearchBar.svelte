<script lang="ts">
	import Icon from './Icon.svelte';

	let {
		value = '',
		loading = false,
		onquery,
		onsearch
	}: {
		value?: string;
		loading?: boolean;
		onquery?: (q: string) => void;
		onsearch?: (q: string) => void;
	} = $props();

	let draft = $derived(value);

	function submit(event: SubmitEvent): void {
		event.preventDefault();
		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}
		onsearch?.(String(new FormData(form).get('q') ?? ''));
	}

	function onInput(event: Event): void {
		if (event.currentTarget instanceof HTMLInputElement) {
			onquery?.(event.currentTarget.value);
		}
	}
</script>

<form class="w-full" role="search" onsubmit={submit}>
	<label class="input input-sm w-full">
		<Icon name="search" class="size-4 opacity-50" />
		<input
			type="search"
			name="q"
			placeholder="Search samples"
			autocomplete="off"
			aria-label="Search samples"
			bind:value={draft}
			oninput={onInput}
		/>
		{#if loading}
			<span class="loading loading-spinner loading-xs" aria-label="Loading"></span>
		{/if}
	</label>
</form>
