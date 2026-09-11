<script lang="ts">
	let { onstopGesture }: { onstopGesture: (event: Event) => void } = $props();

	const popoverId = `sample-actions-${crypto.randomUUID()}`;
	const anchorName = `--${popoverId}`;

	function runAction(event: Event): void {
		onstopGesture(event);
		const popover = event.currentTarget instanceof Element ? event.currentTarget.closest('[popover]') : null;
		if (popover instanceof HTMLElement) popover.hidePopover();
	}

	function positionIfUnanchored(node: HTMLElement) {
		if (CSS.supports('anchor-name', '--x')) return;
		const button = document.querySelector(`[popovertarget="${CSS.escape(node.id)}"]`);
		if (!(button instanceof HTMLElement)) return;

		const place = () => {
			const rect = button.getBoundingClientRect();
			node.style.margin = '0';
			node.style.inset = 'auto';
			node.style.top = `${rect.bottom + 4}px`;
			node.style.left = `${Math.max(8, rect.right - node.offsetWidth)}px`;
		};

		const onToggle = () => {
			if (node.matches(':popover-open')) place();
		};
		node.addEventListener('toggle', onToggle);
		return () => node.removeEventListener('toggle', onToggle);
	}
</script>

<button
	type="button"
	class="btn btn-ghost btn-square btn-xs"
	aria-label="Sample actions"
	popovertarget={popoverId}
	style="anchor-name: {anchorName}"
	onpointerdown={onstopGesture}
	onclick={onstopGesture}
>
	<span class="icon-[lucide--ellipsis-vertical] size-4" aria-hidden="true"></span>
</button>

<ul
	id={popoverId}
	class="dropdown dropdown-end menu menu-sm rounded-box w-52 border border-base-300 bg-base-100 p-2"
	popover
	style="position-anchor: {anchorName}"
	{@attach positionIfUnanchored}
>
	<li>
		<button type="button" onpointerdown={onstopGesture} onclick={runAction}>Rename</button>
	</li>
	<li>
		<button type="button" onpointerdown={onstopGesture} onclick={runAction}>Delete</button>
	</li>
	<li>
		<button type="button" onpointerdown={onstopGesture} onclick={runAction}>Show in folder</button>
	</li>
</ul>
