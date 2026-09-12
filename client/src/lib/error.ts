export const desktopOnlyMessage = 'Open Armarium as the desktop app to cache, drag, or reveal files.'

export function toErrorMessage(caught: unknown): string {
	if (caught instanceof Error) {
		return caught.message;
	}
	if (typeof caught === 'string') {
		return caught;
	}
	return 'Something went wrong';
}
