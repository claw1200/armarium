import { expect, test } from 'vitest';
import { emptyListText, parseLocation } from './locations';

test('parseLocation keeps a known location', () => {
	expect(parseLocation('downloaded')).toBe('downloaded');
	expect(parseLocation('recent')).toBe('recent');
	expect(parseLocation('all')).toBe('all');
	expect(parseLocation('recents')).toBe('all');
	expect(parseLocation(null)).toBe('all');
});

test('emptyListText matches the selected location', () => {
	expect(emptyListText('downloaded')).toBe('No cached samples.');
	expect(emptyListText('recent')).toBe('No samples modified in the last 7 days.');
	expect(emptyListText('all')).toBe('No samples in the library.');
});
