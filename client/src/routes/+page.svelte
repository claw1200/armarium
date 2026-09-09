<script lang="ts">
	import { invoke, isTauri } from '@tauri-apps/api/core';
	import { desktopOnlyMessage, toErrorMessage } from '$lib/error';
	import { fileNameFromPath } from '$lib/file-name';

	type FixtureSample = {
		name: string;
		path: string;
	};

	let sample = $state<FixtureSample | null>(null);
	let error = $state<string | null>(null);

	void loadFixture();

	async function loadFixture(): Promise<void> {
		if (!isTauri()) {
			error = desktopOnlyMessage;
			return;
		}
		try {
			sample = await invoke<FixtureSample>('fixture_sample');
		} catch (caught) {
			error = toErrorMessage(caught);
		}
	}

	async function startDrag(): Promise<void> {
		if (!isTauri()) {
			error = desktopOnlyMessage;
			return;
		}
		error = null;
		try {
			await invoke('start_fixture_drag');
		} catch (caught) {
			error = toErrorMessage(caught);
		}
	}
</script>

<div class="hero min-h-screen">
	<div class="hero-content w-full max-w-xl">
		<div class="card w-full">
			<div class="card-body">
				<h1 class="card-title">Drag proof</h1>
				<p>
					Drag the sample into Finder or a DAW. The file should arrive as
					{sample ? fileNameFromPath(sample.path) : 'kick.wav'}.
				</p>
				<ul class="list">
					<li class="list-row">
						<button
							type="button"
							class="btn list-col-grow"
							disabled={sample === null}
							onpointerdown={startDrag}
						>
							{sample?.name ?? (error ? 'Sample unavailable' : 'Loading sample')}
						</button>
					</li>
				</ul>
				{#if error}
					<div
						role="alert"
						class={['alert', error === desktopOnlyMessage ? 'alert-info' : 'alert-error']}
					>
						{error}
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
