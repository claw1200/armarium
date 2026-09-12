import { expect, test } from 'vitest';
import { parseBpm, parseKey } from './filters';

test('parseKey keeps a pitch-class root', () => {
	expect(parseKey('F#')).toBe('F#');
	expect(parseKey('Cm')).toBe('');
	expect(parseKey('nope')).toBe('');
	expect(parseKey(null)).toBe('');
});

test('parseBpm keeps a known range id', () => {
	expect(parseBpm('110-130')).toBe('110-130');
	expect(parseBpm('150+')).toBe('150+');
	expect(parseBpm('70–90')).toBe('');
	expect(parseBpm(null)).toBe('');
});
