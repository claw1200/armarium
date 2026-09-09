export function waveformAmplitudes(seed: string, count = 40): number[] {
	let n = 2166136261;
	for (let i = 0; i < seed.length; i += 1) {
		n ^= seed.charCodeAt(i);
		n = Math.imul(n, 16777619);
	}
	const amplitudes: number[] = [];
	for (let i = 0; i < count; i += 1) {
		n = Math.imul(n ^ (n >>> 16), 2246822519);
		n = Math.imul(n ^ (n >>> 13), 3266489917);
		n ^= n >>> 16;
		amplitudes.push(0.18 + ((n >>> 0) / 4294967295) * 0.82);
	}
	return amplitudes;
}
