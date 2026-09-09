import { expect, test } from 'vitest';
import { cacheSample } from './cache';
import { desktopOnlyMessage } from './error';

test('cacheSample refuses the browser', async () => {
	await expect(cacheSample('Drums/Kicks/kick.wav')).rejects.toThrow(desktopOnlyMessage);
});
