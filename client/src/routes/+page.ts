import { DEFAULT_PAGE_SIZE, fetchFiles } from '$lib/api';
import { toErrorMessage } from '$lib/error';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q')?.trim() ?? '';
	try {
		return {
			catalog: await fetchFiles({ limit: DEFAULT_PAGE_SIZE, q: q || undefined }, fetch),
			q,
			loadError: null
		};
	} catch (caught) {
		return { catalog: null, q, loadError: toErrorMessage(caught) };
	}
};
