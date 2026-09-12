import { createSubscriber } from 'svelte/reactivity';
import {
	catalogScanSocketUrl,
	parseScanProgress,
	scanPercent,
	type ScanProgress
} from './api';

const idle: ScanProgress = { status: 'idle', done: 0, total: 0 };

export class ScanWatch {
	#snapshot: ScanProgress = idle;
	#listeners = new Set<() => void>();
	#subscribe = createSubscriber((update) => {
		let closed = false;
		let socket: WebSocket | undefined;
		let retry: ReturnType<typeof setTimeout> | undefined;

		const connect = () => {
			socket = new WebSocket(catalogScanSocketUrl());
			socket.addEventListener('message', (event) => {
				const progress = parseScanProgress(String(event.data));
				if (progress === null) {
					return;
				}
				const wasRunning = this.#snapshot.status === 'running';
				this.#snapshot = progress;
				update();
				if (wasRunning && progress.status === 'idle') {
					for (const listener of this.#listeners) {
						listener();
					}
				}
			});
			socket.addEventListener('close', () => {
				if (!closed) {
					retry = setTimeout(connect, 1000);
				}
			});
		};
		connect();
		return () => {
			closed = true;
			clearTimeout(retry);
			socket?.close();
		};
	});

	get running(): boolean {
		this.#subscribe();
		return this.#snapshot.status === 'running';
	}

	get percent(): number {
		this.#subscribe();
		return scanPercent(this.#snapshot);
	}

	get total(): number {
		this.#subscribe();
		return this.#snapshot.total;
	}

	onComplete(listener: () => void): () => void {
		this.#subscribe();
		this.#listeners.add(listener);
		return () => {
			this.#listeners.delete(listener);
		};
	}
}

export const scanWatch = new ScanWatch();
