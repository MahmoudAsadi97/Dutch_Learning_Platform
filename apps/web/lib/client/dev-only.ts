/** Developer-only routes (the UI gallery) exist everywhere except in production. */
export function isDevRoute(appEnv: string | undefined): boolean {
  return appEnv !== "production";
}
