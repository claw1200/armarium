<script lang="ts">
	let {
		kind,
		text,
		onDismiss,
		dismissLabel = 'Dismiss'
	}: {
		kind: 'error' | 'success';
		text: string;
		onDismiss?: () => void;
		dismissLabel?: string;
	} = $props();
</script>

<div role="alert" class="alert text-sm {kind === 'error' ? 'alert-error' : 'alert-success'}">
	<span>{text}</span>
	{#if onDismiss}
		<button type="button" class="btn btn-ghost btn-xs" onclick={onDismiss}>{dismissLabel}</button>
	{/if}
</div>
