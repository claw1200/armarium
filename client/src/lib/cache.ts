import { invoke, isTauri } from '@tauri-apps/api/core';
import { apiBase } from './api';
import { desktopOnlyMessage } from './error';

export async function cacheSample(relativePath: string): Promise<string> {
	if (!isTauri()) {
		throw new Error(desktopOnlyMessage);
	}
	return invoke<string>('cache_sample', { relativePath, apiBase: apiBase() });
}
