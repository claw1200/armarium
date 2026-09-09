export type Breadcrumb = {
	name: string;
	path: string;
};

export function breadcrumbs(folderPath: string): Breadcrumb[] {
	const crumbs: Breadcrumb[] = [{ name: 'Library', path: '' }];
	if (!folderPath) {
		return crumbs;
	}
	let current = '';
	for (const part of folderPath.split('/').filter(Boolean)) {
		current = current ? `${current}/${part}` : part;
		crumbs.push({ name: part, path: current });
	}
	return crumbs;
}

export function folderHref(folderPath: string): '/' | `/?${string}` {
	if (!folderPath) {
		return '/';
	}
	return `/?path=${encodeURIComponent(folderPath)}`;
}
