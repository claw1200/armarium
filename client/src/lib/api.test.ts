import { expect, test } from 'vitest';
import { audioUrl, catalogEntriesUrl, fetchListing } from './api';

const BASE = 'http://127.0.0.1:8000';

test('catalog url omits path at the library root', () => {
	expect(catalogEntriesUrl('', BASE)).toBe('http://127.0.0.1:8000/catalog/entries');
});

test('catalog url includes a nested folder path', () => {
	expect(catalogEntriesUrl('Drums/Kicks', BASE)).toBe(
		'http://127.0.0.1:8000/catalog/entries?path=Drums%2FKicks'
	);
});

test('audio url encodes each path segment', () => {
	expect(audioUrl('Pack/kick 01.wav', BASE)).toBe(
		'http://127.0.0.1:8000/audio/Pack/kick%2001.wav'
	);
});

test('fetchListing returns json from a successful response', async () => {
	const listing = {
		path: 'Drums/Kicks',
		folders: [],
		files: [
			{
				name: 'kick.wav',
				path: 'Drums/Kicks/kick.wav',
				size_bytes: 100,
				format: 'wav',
				duration_seconds: 0.1,
				sample_rate: 44100,
				channels: 1
			}
		]
	};
	const result = await fetchListing('Drums/Kicks', async () => new Response(JSON.stringify(listing)), BASE);
	expect(result).toEqual(listing);
});

test('fetchListing throws when the catalog is unavailable', async () => {
	await expect(
		fetchListing('Drums', async () => new Response('nope', { status: 500 }), BASE)
	).rejects.toThrow('Catalog request failed (500)');
});
