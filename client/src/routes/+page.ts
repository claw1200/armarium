import { fetchListing } from '$lib/api';
import { toErrorMessage } from '$lib/error';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url }) => {
	const path = url.searchParams.get('path') ?? '';
	try {
		return { listing: await fetchListing(path), loadError: null };
	} catch (caught) {
		return { listing: null, loadError: toErrorMessage(caught) };
	}
};
