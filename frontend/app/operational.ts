const APP_VERSION = "0.1.0";

export function healthResponse(): Response {
  return Response.json({ status: "ok", version: APP_VERSION });
}

export function versionResponse(): Response {
  return Response.json({ version: APP_VERSION });
}
