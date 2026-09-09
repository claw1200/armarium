import { expect, test } from 'vitest';
import { toErrorMessage } from './error';

test('uses an Error message', () => {
	expect(toErrorMessage(new Error('file not found'))).toBe('file not found');
});

test('uses a string as-is', () => {
	expect(toErrorMessage('file not found: kick.wav')).toBe('file not found: kick.wav');
});

test('falls back when the value is not a message', () => {
	expect(toErrorMessage({ reason: 'nope' })).toBe('Something went wrong');
});
