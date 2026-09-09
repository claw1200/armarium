import { expect, test } from 'vitest';
import { formatDuration, formatSize } from './format';

test('formatDuration uses seconds under a minute', () => {
	expect(formatDuration(0.1)).toBe('0.10s');
	expect(formatDuration(null)).toBe('—');
});

test('formatDuration uses minutes after a minute', () => {
	expect(formatDuration(90)).toBe('1:30');
});

test('formatSize picks a readable unit', () => {
	expect(formatSize(500)).toBe('500 B');
	expect(formatSize(1536)).toBe('1.5 KB');
	expect(formatSize(2_000_000)).toBe('1.9 MB');
});
