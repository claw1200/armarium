<script lang="ts">
	let {
		text,
		actionLabel,
		actionPrimary = false,
		onAction
	}: {
		text: string;
		actionLabel?: string;
		actionPrimary?: boolean;
		onAction?: () => void;
	} = $props();
</script>

<div class="flex flex-col items-center gap-3 px-6 py-12 text-center text-sm opacity-80">
	<p>{text}</p>
	{#if actionLabel && onAction}
		<button type="button" class={['btn btn-sm', actionPrimary ? 'btn-primary' : 'btn-outline']} onclick={onAction}>
			{actionLabel}
		</button>
	{/if}
</div>
