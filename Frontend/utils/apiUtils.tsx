// my-next-app/utils/apiUtils.ts

export async function callApi(
  url: string,
  options: RequestInit = {}
) {
  try {
    const headers = new Headers(options.headers || {});

    const isFormData = options.body instanceof FormData;

    // ✅ Only set JSON header if NOT FormData
    if (!isFormData) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }

    const contentType = response.headers.get("content-type");

    if (contentType?.includes("application/json")) {
      return await response.json();
    }

    return response;

  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}
