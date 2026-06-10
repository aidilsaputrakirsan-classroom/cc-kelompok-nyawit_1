import { GATEWAY_URL } from "../config/gateway";
import { getFriendlyApiErrorMessage, isServiceUnavailable } from "./apiError";

export async function gatewayFetch(
  path: string,
  init?: RequestInit
): Promise<Response> {
  const url = path.startsWith("http") ? path : `${GATEWAY_URL}${path}`;

  try {
    const response = await fetch(url, init);

    if (isServiceUnavailable(response.status)) {
      throw new Error("Service temporarily unavailable");
    }

    return response;
  } catch (error) {
    if (error instanceof Error && error.message === "Service temporarily unavailable") {
      throw error;
    }
    throw new Error(getFriendlyApiErrorMessage(error));
  }
}
