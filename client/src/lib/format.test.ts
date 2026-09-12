import { expect, test } from 'vitest';
import { fileStem, formatAudioFormat, formatBpm, formatDuration, formatKey, formatSize } from './format';

test('formatBpm shows a dash when missing', () => {
	expect(formatBpm(null)).toBe('—');
	expect(formatBpm(128)).toBe('128');
	expect(formatBpm(87.5)).toBe('87.5');
});

test('formatKey shows a dash when missing', () => {
	expect(formatKey(null)).toBe('—');
	expect(formatKey('C#m')).toBe('C#m');
});

test('formatDuration uses minutes and seconds', () => {
	expect(formatDuration(0.1)).toBe('0:01');
	expect(formatDuration(1.4)).toBe('0:01');
	expect(formatDuration(90)).toBe('1:30');
	expect(formatDuration(null)).toBe('—');
});

test('formatAudioFormat uppercases the extension', () => {
	expect(formatAudioFormat('wav')).toBe('WAV');
});

test('fileStem drops the last extension', () => {
	expect(fileStem('kick.wav')).toBe('kick');
	expect(fileStem('loop.aif')).toBe('loop');
	expect(fileStem('no-ext')).toBe('no-ext');
	expect(fileStem('.hidden')).toBe('.hidden');
});

test('formatSize picks a readable unit', () => {
	expect(formatSize(500)).toBe('500 B');
	expect(formatSize(1536)).toBe('1.5 KB');
	expect(formatSize(2_000_000)).toBe('1.9 MB');
});
