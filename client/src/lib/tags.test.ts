import { expect, test } from 'vitest';
import { parseTags, setFacetTag, tagForFacet } from './tags';

test('parseTags keeps one slug per facet in form-role-function order', () => {
	expect(parseTags(['kick', 'loop', 'melody', 'snare', 'nope'])).toEqual([
		'loop',
		'kick',
		'melody'
	]);
});

test('parseTags drops unknown slugs', () => {
	expect(parseTags(['drums', 'cinematic'])).toEqual([]);
});

test('tagForFacet reads the selected slug for a facet', () => {
	expect(tagForFacet(['loop', 'kick'], 'form')).toBe('loop');
	expect(tagForFacet(['loop', 'kick'], 'function')).toBe('');
});

test('setFacetTag replaces the slug for one facet and leaves the others', () => {
	expect(setFacetTag(['loop'], 'role', 'kick')).toEqual(['loop', 'kick']);
	expect(setFacetTag(['loop', 'kick'], 'form', 'one-shot')).toEqual(['one-shot', 'kick']);
	expect(setFacetTag(['loop', 'kick'], 'role', '')).toEqual(['loop']);
});

test('setFacetTag ignores a slug that does not belong to the facet', () => {
	expect(setFacetTag(['loop'], 'form', 'kick')).toEqual(['loop']);
});
