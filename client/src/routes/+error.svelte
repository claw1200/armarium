<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';

	const notFound = $derived(page.status === 404);
</script>

<div class="flex min-h-dvh flex-col items-center justify-center gap-6 bg-base-200 px-4 text-center">
	<p class="text-8xl font-black text-base-content/20">{page.status}</p>
	<div class="space-y-2">
		<h1 class="text-2xl font-semibold tracking-tight">
			{notFound ? 'Page not found' : 'Something went wrong'}
		</h1>
		<p class="text-sm opacity-80">
			{notFound ? "That page doesn't exist." : 'Reload and try again.'}
		</p>
	</div>
	<a href={resolve('/')} class="btn btn-primary">Back to library</a>
</div>
