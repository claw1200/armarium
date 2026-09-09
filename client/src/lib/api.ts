export type CatalogFolder = {
	name: string;
	path: string;
};

export type CatalogFile = {
	name: string;
	path: string;
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

export const DEFAULT_API_BASE = 'http://127.0.0.1:8000';

type ApiEnv = { PUBLIC_ARMARIUM_API?: string };

export function apiBase(env: ApiEnv = import.meta.env as ApiEnv): string {
	const configured = env.PUBLIC_ARMARIUM_API?.trim();
	if (configured) {
		return configured.replace(/\/$/, '');
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
