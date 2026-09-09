import { expect, test } from 'vitest';
import { waveformAmplitudes } from './waveform';

test('waveformAmplitudes is deterministic for a seed', () => {
	expect(waveformAmplitudes('kick.wav', 8)).toEqual(waveformAmplitudes('kick.wav', 8));
});

test('waveformAmplitudes respects count and stays in range', () => {
	const bars = waveformAmplitudes('snare.wav', 12);
	expect(bars).toHaveLength(12);
	expect(bars.every((value) => value >= 0.18 && value <= 1)).toBe(true);
});
