import { expect, test } from 'vitest';
import { cacheSample, listCached, listCachedFiles, revealLibrary, startCachedDrag } from './cache';
import { desktopOnlyMessage } from './error';

test('cacheSample refuses the browser', async () => {
	await expect(cacheSample('Drums/Kicks/kick.wav')).rejects.toThrow(desktopOnlyMessage);
});

test('listCached is empty outside Tauri', async () => {
	await expect(listCached(['Drums/Kicks/kick.wav'])).resolves.toEqual([]);
});

test('listCachedFiles is empty outside Tauri', async () => {
	await expect(listCachedFiles()).resolves.toEqual([]);
});

test('startCachedDrag refuses the browser', async () => {
	await expect(startCachedDrag('Drums/Kicks/kick.wav')).rejects.toThrow(desktopOnlyMessage);
});

test('revealLibrary refuses the browser', async () => {
	await expect(revealLibrary('Drums/Kicks/kick.wav')).rejects.toThrow(desktopOnlyMessage);
});
