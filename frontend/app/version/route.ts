import { versionResponse } from "@/app/operational";

export function GET(): Response {
  return versionResponse();
}
