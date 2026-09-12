import { env } from '$env/dynamic/public';

export type CatalogFolder = {
	name: string;
	path: string;
};

export type CatalogFile = {
	name: string;
	path: string;
	parent_path: string;
	size_bytes: number;
	format: string;
	duration_seconds: number | null;
	sample_rate: number | null;
	channels: number | null;
	bpm: number | null;
	key: string | null;
	tags: string[];
};

export type CatalogListing = {
	path: string;
	folders: CatalogFolder[];
	files: CatalogFile[];
};

export type CatalogPage = {
	items: CatalogFile[];
	total: number;
	limit: number;
	offset: number;
};

export type CatalogFilesQuery = {
	offset?: number;
	limit?: number;
	prefix?: string;
	q?: string;
	sort?: 'path' | 'name' | 'duration';
	tags?: string[];
};

export const DEFAULT_API_BASE = 'http://127.0.0.1:8000';
export const DEFAULT_PAGE_SIZE = 50;

export function apiBase(configured: string | undefined = env.PUBLIC_ARMARIUM_API): string {
	const trimmed = configured?.trim();
	if (trimmed) {
		return trimmed.replace(/\/$/, '');
	}
	return DEFAULT_API_BASE;
}

export function catalogEntriesUrl(folderPath: string, base = apiBase()): string {
	const url = new URL('catalog/entries', `${base}/`);
	if (folderPath) {
		url.searchParams.set('path', folderPath);
	}
	return url.toString();
}

export function catalogFilesUrl(query: CatalogFilesQuery = {}, base = apiBase()): string {
	const url = new URL('catalog/files', `${base}/`);
	const offset = query.offset ?? 0;
	const limit = query.limit ?? DEFAULT_PAGE_SIZE;
	if (offset > 0) {
		url.searchParams.set('offset', String(offset));
	}
	if (limit !== DEFAULT_PAGE_SIZE) {
		url.searchParams.set('limit', String(limit));
	}
	if (query.prefix) {
		url.searchParams.set('prefix', query.prefix);
	}
	if (query.q) {
		url.searchParams.set('q', query.q);
	}
	if (query.sort && query.sort !== 'path') {
		url.searchParams.set('sort', query.sort);
	}
	for (const tag of query.tags ?? []) {
		url.searchParams.append('tag', tag);
	}
	return url.toString();
}

export function audioUrl(relativePath: string, base = apiBase()): string {
	const encoded = relativePath
		.split('/')
		.filter((part) => part.length > 0)
		.map(encodeURIComponent)
		.join('/');
	return `${base}/audio/${encoded}`;
}

export type ScanProgress = {
	status: 'idle' | 'running';
	done: number;
	total: number;
};

export function catalogScanSocketUrl(base = apiBase()): string {
	const url = new URL('catalog/scan', `${base.replace(/\/$/, '')}/`);
	url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
	return url.toString();
}

export function parseScanProgress(data: string): ScanProgress | null {
	let parsed: unknown;
	try {
		parsed = JSON.parse(data);
	} catch {
		return null;
	}
	if (parsed === null || typeof parsed !== 'object') {
		return null;
	}
	const record = parsed as Record<string, unknown>;
	if (record.status !== 'idle' && record.status !== 'running') {
		return null;
	}
	if (typeof record.done !== 'number' || typeof record.total !== 'number') {
		return null;
	}
	if (!Number.isFinite(record.done) || !Number.isFinite(record.total)) {
		return null;
	}
	return {
		status: record.status,
		done: record.done,
		total: record.total
	};
}

export function scanPercent(progress: ScanProgress): number {
	if (progress.total <= 0) {
		return 0;
	}
	return Math.min(100, Math.round((progress.done / progress.total) * 100));
}

export async function fetchListing(
	folderPath: string,
	fetchImpl: typeof fetch = fetch,
	base = apiBase()
): Promise<CatalogListing> {
	const response = await fetchImpl(catalogEntriesUrl(folderPath, base));
	if (!response.ok) {
		throw new Error(`Catalog request failed (${response.status})`);
	}
	return (await response.json()) as CatalogListing;
}

export async function fetchFiles(
	query: CatalogFilesQuery = {},
	fetchImpl: typeof fetch = fetch,
	base = apiBase()
): Promise<CatalogPage> {
	const response = await fetchImpl(catalogFilesUrl(query, base));
	if (!response.ok) {
		throw new Error(`Catalog request failed (${response.status})`);
	}
	return (await response.json()) as CatalogPage;
}
