import { expect, test } from 'vitest';
import { fileNameFromPath } from './file-name';

test('reads a posix path', () => {
	expect(fileNameFromPath('/library/Drums/Kicks/kick.wav')).toBe('kick.wav');
});

test('reads a windows path', () => {
	expect(fileNameFromPath('C:\\library\\Drums\\Kicks\\kick.wav')).toBe('kick.wav');
});

test('reads a bare filename', () => {
	expect(fileNameFromPath('kick.wav')).toBe('kick.wav');
});
