import { DEFAULT_PAGE_SIZE, fetchFiles } from '$lib/api';
import { listCachedFiles } from '$lib/cache';
import { toErrorMessage } from '$lib/error';
import { parseBpm, parseKey } from '$lib/filters';
import { parseLocation } from '$lib/locations';
import { parseTags } from '$lib/tags';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q')?.trim() ?? '';
	const tags = parseTags(url.searchParams.getAll('tag'));
	const key = parseKey(url.searchParams.get('key'));
	const bpm = parseBpm(url.searchParams.get('bpm'));
	const location = parseLocation(url.searchParams.get('location'));
	const recent = location === 'recent';
	let paths: string[] | undefined;
	try {
		paths = location === 'downloaded' ? await listCachedFiles() : undefined;
		return {
			catalog: await fetchFiles(
				{
					limit: DEFAULT_PAGE_SIZE,
					q: q || undefined,
					tags: tags.length > 0 ? tags : undefined,
					key: key || undefined,
					bpm: bpm || undefined,
					paths,
					recent: recent || undefined
				},
				fetch
			),
			q,
			tags,
			key,
			bpm,
			location,
			paths,
			recent,
			loadError: null
		};
	} catch (caught) {
		return {
			catalog: null,
			q,
			tags,
			key,
			bpm,
			location,
			paths,
			recent,
			loadError: toErrorMessage(caught)
		};
	}
};
