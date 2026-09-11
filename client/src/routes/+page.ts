import { DEFAULT_PAGE_SIZE, fetchFiles } from '$lib/api';
import { toErrorMessage } from '$lib/error';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
	const parsed = Number(url.searchParams.get('offset') ?? '0');
	const offset = Number.isInteger(parsed) && parsed >= 0 ? parsed : 0;
	const q = url.searchParams.get('q')?.trim() ?? '';
	try {
		return {
			catalog: await fetchFiles({ offset, limit: DEFAULT_PAGE_SIZE, q: q || undefined }, fetch),
			q,
			loadError: null
		};
	} catch (caught) {
		return { catalog: null, q, loadError: toErrorMessage(caught) };
	}
};
