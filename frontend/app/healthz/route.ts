import { healthResponse } from "@/app/operational";

export function GET(): Response {
  return healthResponse();
}
