import { invoke, isTauri } from '@tauri-apps/api/core';
import { apiBase } from './api';
import { desktopOnlyMessage } from './error';

export type CachedDrag =
	| { status: 'started'; path: string }
	| { status: 'needsDownload' };

export async function cacheSample(relativePath: string): Promise<string> {
	if (!isTauri()) {
		throw new Error(desktopOnlyMessage);
	}
	return invoke<string>('cache_sample', { relativePath, apiBase: apiBase() });
}

export async function listCached(relativePaths: string[]): Promise<string[]> {
	if (!isTauri() || relativePaths.length === 0) {
		return [];
	}
	return invoke<string[]>('cached_paths', { relativePaths });
}

export async function startCachedDrag(relativePath: string): Promise<CachedDrag> {
	if (!isTauri()) {
		throw new Error(desktopOnlyMessage);
	}
	return invoke<CachedDrag>('start_cached_drag', { relativePath });
}
