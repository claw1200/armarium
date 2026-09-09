import { expect, test } from 'vitest';
import { breadcrumbs, folderHref } from './catalog-path';

test('breadcrumbs start at the library root', () => {
	expect(breadcrumbs('')).toEqual([{ name: 'Library', path: '' }]);
});

test('breadcrumbs include each nested folder', () => {
	expect(breadcrumbs('Drums/Kicks')).toEqual([
		{ name: 'Library', path: '' },
		{ name: 'Drums', path: 'Drums' },
		{ name: 'Kicks', path: 'Drums/Kicks' }
	]);
});

test('folder href encodes the catalog path', () => {
	expect(folderHref('')).toBe('/');
	expect(folderHref('Drums/Kicks')).toBe('/?path=Drums%2FKicks');
});
