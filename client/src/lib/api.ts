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
	sort?: 'path' | 'name' | 'duration';
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
	if (query.sort && query.sort !== 'path') {
		url.searchParams.set('sort', query.sort);
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
